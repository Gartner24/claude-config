"""Tests for post.slides() and batch.run(). Run: python3 test_post_batch.py"""
import os, random, subprocess, sys, tempfile, unittest

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

    def test_links_file(self):
        p = os.path.join(self.out, "links.txt")
        open(p, "w").write("# mine\n\nhttps://a/p/1/\n  https://a/p/2/  \n  # later\n")
        self.assertEqual(batch.links(p), ["https://a/p/1/", "https://a/p/2/"])


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
