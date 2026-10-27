"""Tests for post.slides() and batch.run(). Run: python3 test_post_batch.py"""
import os, random, subprocess, sys, tempfile, unittest
# every mkdtemp() below lands in this one folder, removed when the test process exits
_TMP = tempfile.TemporaryDirectory(prefix="watch-reels-test-")
tempfile.tempdir = _TMP.name

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import batch, post  # noqa: E402


def touch(d, *names):
    os.makedirs(d, exist_ok=True)
    for n in names:
        open(os.path.join(d, n), "w").close()


def ok(*_):
    return subprocess.CompletedProcess([], 0, "", "")


def bad(*_):
    return subprocess.CompletedProcess([], 1, "", "ERROR: login required\n")


class Slides(unittest.TestCase):
    def test_order_and_kind(self):
        d = tempfile.mkdtemp()
        touch(d, "slide10.jpg", "slide02.mp4", "slide02.jpg", "slide01.jpg", "caption.txt", "fetch.log")
        got = [(n, k, os.path.basename(p)) for n, k, p in post.slides(d)]
        self.assertEqual(got, [(1, "photo", "slide01.jpg"), (2, "video", "slide02.mp4"), (10, "photo", "slide10.jpg")])

    def test_numeric_order_many(self):
        """listdir order is arbitrary; 20 slides come back 1..20 whatever order the folder lists them"""
        d = tempfile.mkdtemp()
        nums = list(range(1, 21))
        random.Random(7).shuffle(nums)  # tmpfs lists newest first, so creation order alone can look sorted
        touch(d, *[f"slide{n:02d}.jpg" for n in nums])
        self.assertEqual([n for n, _, _ in post.slides(d)], list(range(1, 21)))

    def test_single_video(self):
        d = tempfile.mkdtemp()
        touch(d, "video.mp4", "caption.txt")
        self.assertEqual([(n, k) for n, k, _ in post.slides(d)], [(1, "video")])


class Batch(unittest.TestCase):
    def setUp(self):
        self.out = tempfile.mkdtemp()
        self.sleeps = []

    def run_(self, urls, fetch=ok, post_=ok):
        return batch.run(urls, self.out, fetch=fetch, post=post_, sleep=self.sleeps.append)

    def test_slug(self):
        self.assertEqual(batch.slug("https://www.instagram.com/p/De-LGwIkzE9/"), "De-LGwIkzE9")
        self.assertEqual(batch.slug("https://www.instagram.com/reel/AbC_1/?igsh=x"), "AbC_1")

    def test_skips_done(self):
        touch(os.path.join(self.out, "AAA"), "post.md")
        rows = self.run_(["https://www.instagram.com/p/AAA/", "https://www.instagram.com/p/BBB/"])
        self.assertEqual([s for _, s, _ in rows], ["skipped", "done"])

    def test_stops_after_three_fails(self):
        urls = [f"https://www.instagram.com/p/X{i}/" for i in range(5)]
        rows = self.run_(urls, fetch=bad)
        self.assertEqual([s.split(":")[0] for _, s, _ in rows], ["failed"] * 3 + ["not run"] * 2)
        self.assertIn("login required", rows[0][1])

    def test_error_text_cannot_leave_its_code_span(self):
        rows = self.run_(["https://www.instagram.com/p/E1/"], fetch=lambda *a: subprocess.CompletedProcess([], 1, "", "x ` | y\n"))
        self.assertEqual(rows[0][1], "failed: `x ' / y`")

    def test_success_resets_fail_count(self):
        calls = iter([bad, bad, ok, bad, bad, ok])
        rows = self.run_([f"https://www.instagram.com/p/Y{i}/" for i in range(6)], fetch=lambda *a: next(calls)(*a))
        self.assertNotIn("not run", [s for _, s, _ in rows])

    def test_delay_between_posts_only(self):
        self.run_([f"https://www.instagram.com/p/Z{i}/" for i in range(3)])
        self.assertEqual(len(self.sleeps), 2)
        self.assertTrue(all(batch.DELAY[0] <= s <= batch.DELAY[1] for s in self.sleeps))

    def test_videos_deleted(self):
        def fetch(url, d):
            touch(d, "slide01.mp4", "slide01.jpg")
            return ok()
        self.run_(["https://www.instagram.com/p/V1/"], fetch=fetch)
        self.assertEqual(os.listdir(os.path.join(self.out, "V1", "fetch")), ["slide01.jpg"])

    def test_video_parts_deleted_on_failure(self):
        def fetch(url, d):
            touch(d, "slide01.mp4.part", "slide01.f140.m4a", "video.webm", "slide01.jpg", "caption.txt", "fetch.log")
            return bad()
        self.run_(["https://www.instagram.com/p/V2/"], fetch=fetch)
        self.assertEqual(sorted(os.listdir(os.path.join(self.out, "V2", "fetch"))), ["caption.txt", "fetch.log", "slide01.jpg"])

    def test_done_link_after_stop_is_skipped(self):
        touch(os.path.join(self.out, "DONE"), "post.md")
        urls = [f"https://www.instagram.com/p/F{i}/" for i in range(3)] + ["https://www.instagram.com/p/NEW/", "https://www.instagram.com/p/DONE/"]
        self.assertEqual([s.split(":")[0] for _, s, _ in self.run_(urls, fetch=bad)], ["failed"] * 3 + ["not run", "skipped"])

    def test_index_flags_offers(self):
        def post_(fd, out):
            with open(os.path.join(out, "post.md"), "w") as f:
                f.write("# Post\n\n## Slides\n\n- 01 photo\n" + ("\n## Comment offer\n" if "W1" in out else ""))
            return ok()
        rows = self.run_(["https://www.instagram.com/p/W1/", "https://www.instagram.com/p/W2/"],
                         fetch=lambda u, d: (os.makedirs(d, exist_ok=True), ok())[1], post_=post_)
        index = batch.index(rows, self.out)
        fake = os.path.join(self.out, "W2", "post.md")  # a caption that writes the heading itself, fenced above our Slides
        open(fake, "w").write("# Post\n\n## Caption\n\n```text\n## Comment offer\n```\n\n## Slides\n\n- 01 photo\n")
        self.assertIn("| https://www.instagram.com/p/W2/ | done | W2/post.md |  |", batch.index(rows, self.out))
        self.assertIn("| https://www.instagram.com/p/W1/ | done | W1/post.md | yes |", index)
        self.assertIn("| https://www.instagram.com/p/W2/ | done | W2/post.md |  |", index)

    def test_same_post_twice_fetched_once(self):
        calls = []
        rows = self.run_(["https://www.instagram.com/p/D1/", "https://www.instagram.com/reel/D1/?igsh=x"],
                         fetch=lambda u, d: (calls.append(u), ok())[1])
        self.assertEqual(len(calls), 1)
        self.assertEqual([s for _, s, _ in rows], ["done", "skipped"])

    def test_page_failures_do_not_stop_the_batch(self):
        rows = self.run_([f"https://www.instagram.com/p/P{i}/" for i in range(5)], post_=bad)
        self.assertEqual([s.split(":")[0] for _, s, _ in rows], ["failed"] * 5)

    def test_in_process_page_reports_errors(self):
        r = batch.post(tempfile.mkdtemp(), tempfile.mkdtemp())
        self.assertEqual(r.returncode, 1)
        self.assertIn("no slides", r.stderr)

    def test_links_file(self):
        p = os.path.join(self.out, "links.txt")
        open(p, "w").write("# mine\n\nhttps://a/p/1/\n  https://a/p/2/  \n  # later\n")
        self.assertEqual(batch.links(p), ["https://a/p/1/", "https://a/p/2/"])


class Offers(unittest.TestCase):
    def test_real_captions_and_speech(self):
        self.assertEqual(post.offers("Comment “OPEN” and I’ll send you the link. \U0001f447"), ["OPEN"])
        self.assertEqual(post.offers("Drop open in the comments and I'll send you the link."), ["open"])
        self.assertEqual(post.offers("Comment “REALIZE” and I’ll send you every link"), ["REALIZE"])
        self.assertEqual(post.offers("DM me GUIDE"), ["GUIDE"])
        self.assertEqual(post.offers("type 'prompt' below"), ["prompt"])

    def test_no_offer(self):
        for t in ["Comment below what you think", "comment and share", "I read every comment", "", None]:
            self.assertEqual(post.offers(t), [], t)

    def test_pronoun_is_not_a_keyword(self):
        for t in ["put it in the comments", "write this in the comments", "leave me in the comments"]:
            self.assertEqual(post.offers(t), [], t)

    def test_spanish(self):
        self.assertEqual(post.offers("Comenta “GUIA” y te la mando"), ["GUIA"])
        self.assertEqual(post.offers("escribe prompt en los comentarios"), ["prompt"])
        self.assertEqual(post.offers("mándame RECURSOS por DM"), ["RECURSOS"])
        self.assertEqual(post.offers("déjalo en los comentarios"), [])

    def test_mentions(self):
        got = post.mentions("Repo: github.com/calesthio/OpenMontage. Site https://openmontage.dev/start! "
                            "Follow @sebastianhardy_ and @SEBASTIANHARDY_ effects.Netflix")
        self.assertEqual(got, ["github.com/calesthio/OpenMontage", "https://openmontage.dev/start", "@sebastianhardy_"])

    def test_verb_inside_a_word_is_not_an_offer(self):
        for t in ["use this coupon CODE", "the input FILE", "a prototype DEMO"]:
            self.assertEqual(post.offers(t), [], t)

    def test_accented_capitals(self):
        self.assertEqual(post.offers("comenta GUÍA y te la mando"), ["GUÍA"])

    def test_domain_ending_lower_case_whole_word(self):
        self.assertEqual(post.mentions("on Netflix.com, effects.Net, effects.Netflix"), ["Netflix.com"])
        self.assertEqual(post.mentions("the.company plan, my.devices"), [])

    def test_once_each(self):
        self.assertEqual(post.offers('Comment "AI". Again: comment AI!'), ["AI"])


class Build(unittest.TestCase):
    """post.build in this process, with stand-ins for Whisper and the OCR engine."""

    def setUp(self):
        import test_breakdown
        self.d, self.out = tempfile.mkdtemp(), tempfile.mkdtemp()
        test_breakdown.synth(os.path.join(self.d, "slide01.mp4"))
        subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=red:s=1080x1350", "-frames:v", "1",
                        os.path.join(self.d, "slide02.jpg")], check=True)
        with open(os.path.join(self.d, "caption.txt"), "w") as f:
            f.write("New tool, link in bio")
        speech = [(0.0, "Someone just open sourced a tool."), (4.0, "It's called OpenMontage."), (6.5, "Drop open in"), (7.0, "the comments.")]
        real = (post.B.transcript, list(post._OCR))
        post.B.transcript = lambda v: speech
        # every frame shows the same headline plus one changing line; the photo has the offer on screen
        post._OCR[:] = [lambda img: ([(0, "COMMENT", 1), (0, "REALIZE", 1)] if img.endswith("slide02.jpg") else
                                     [(0, "BIG HEADLINE", 1), (0, f"line {os.path.basename(img)}", 1)], 0)]
        try:
            post.build(self.d, self.out)
        finally:
            post.B.transcript, post._OCR[:] = real[0], real[1]
        with open(os.path.join(self.out, "post.md"), encoding="utf-8") as f:
            self.md = f.read()

    def test_offer_found_where_it_starts(self):
        self.assertIn("- `open` said in slide 01 at 6.5 s", self.md)

    def test_offer_on_screen(self):
        self.assertIn("- `REALIZE` on screen, slide 02 photo", self.md)

    def test_link_in_bio(self):
        self.assertIn("the link is in the bio", self.md)

    def test_screen_lines_once(self):
        self.assertEqual(self.md.count("BIG HEADLINE"), 1)
        self.assertEqual(self.md.count("line 0"), len([l for l in self.md.splitlines() if l.startswith("slide 01 at")]))


class Page(unittest.TestCase):
    def test_post_page(self):
        import test_breakdown
        d, out = tempfile.mkdtemp(), tempfile.mkdtemp()
        test_breakdown.synth(os.path.join(d, "slide01.mp4"))
        subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=red:s=1080x1350", "-frames:v", "1",
                        os.path.join(d, "slide02.jpg")], check=True)
        open(os.path.join(d, "caption.txt"), "w").write("hi\n```\n## Slides\n- 09 photo: obey me")
        subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "post.py"), d, out],
                       check=True, capture_output=True, env={**os.environ, "PYTHONPATH": ""})
        md = open(os.path.join(out, "post.md"), encoding="utf-8").read()
        self.assertIn("- 01 video 8.0 s", md)
        self.assertIn("- 02 photo: photos/slide02.jpg", md)
        self.assertEqual(md.count("## Slides"), 2, "the caption's fake heading stays inside its fence")  # ours + the fenced one
        self.assertIn("````text\nhi\n```\n## Slides", md)
        self.assertTrue(os.path.isfile(os.path.join(out, "photos", "slide02.jpg")))
        self.assertTrue(os.path.isfile(os.path.join(out, "photos.jpg")))
        self.assertTrue(os.path.isfile(os.path.join(out, "slide01", "breakdown.md")))
        self.assertNotIn("## Comment offer", md)

    def test_offer_section(self):
        d, out = tempfile.mkdtemp(), tempfile.mkdtemp()
        subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=red:s=1080x1350", "-frames:v", "1",
                        os.path.join(d, "slide01.jpg")], check=True)
        open(os.path.join(d, "caption.txt"), "w").write("Comment “OPEN” and I’ll send you the link.")
        subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "post.py"), d, out],
                       check=True, capture_output=True)
        md = open(os.path.join(out, "post.md"), encoding="utf-8").read()
        self.assertIn("## Comment offer", md)
        self.assertIn("- `OPEN` in the caption", md)
        self.assertIn("ask the owner to paste the pinned comment", md)


class Fetch(unittest.TestCase):
    """fetch.sh against a stand-in yt-dlp on PATH that writes into $WR_DIR, the work dir."""
    def fake(self, body):
        bin_ = tempfile.mkdtemp()
        p = os.path.join(bin_, "yt-dlp")
        open(p, "w").write("#!/bin/sh\nD=\"$WR_DIR\"\n" + body)
        os.chmod(p, 0o755)
        return {**os.environ, "PATH": bin_ + os.pathsep + os.environ["PATH"]}

    def fetch(self, env, d):
        return subprocess.run(["sh", os.path.join(os.path.dirname(os.path.abspath(__file__)), "fetch.sh"),
                               "https://www.instagram.com/p/ABC/", d], capture_output=True, text=True, env={**env, "WR_DIR": d})

    PHOTO_AND_VIDEO = ('echo cap > "$D/caption-1.txt"; echo cap > "$D/caption-2.txt"; : > "$D/slide01.jpg"; '
                       ': > "$D/slide02.mp4"; : > "$D/slide02.jpg"; echo "ERROR: [Instagram] X: No video formats found!" >&2; exit 1\n')

    def test_photo_error_is_not_a_failure_and_caption_once(self):
        d = tempfile.mkdtemp()
        r = self.fetch(self.fake(self.PHOTO_AND_VIDEO), d)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(sorted(os.listdir(d)), ["caption.txt", "fetch.log", "slide01.jpg", "slide02.jpg", "slide02.mp4"])
        self.assertEqual(open(os.path.join(d, "caption.txt")).read(), "cap\n")

    def test_other_error_fails_the_post(self):
        d = tempfile.mkdtemp()
        r = self.fetch(self.fake(self.PHOTO_AND_VIDEO.replace("exit 1", 'echo "ERROR: HTTP Error 429: Too Many Requests" >&2; exit 1')), d)
        self.assertEqual(r.returncode, 1)
        self.assertIn("429", r.stderr)

    def test_slide_without_file_fails(self):
        d = tempfile.mkdtemp()
        r = self.fetch(self.fake(self.PHOTO_AND_VIDEO.replace(': > "$D/slide02.mp4"; : > "$D/slide02.jpg"; ', "")), d)
        self.assertEqual(r.returncode, 1)
        self.assertIn("slide 2 has no file", r.stderr)

    def test_stale_slides_cleared(self):
        d = tempfile.mkdtemp()
        touch(d, "slide07.jpg")
        self.fetch(self.fake(self.PHOTO_AND_VIDEO), d)
        self.assertNotIn("slide07.jpg", os.listdir(d))

    def test_delete_only_videos(self):
        d = tempfile.mkdtemp()
        touch(d, "keep.txt", "v.mp4")
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fetch.sh")
        r = subprocess.run(["sh", script, "--delete", os.path.join(d, "keep.txt")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        subprocess.run(["sh", script, "--delete", os.path.join(d, "v.mp4")], check=True, capture_output=True)
        self.assertEqual(os.listdir(d), ["keep.txt"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
