"""The watch-reels skill's own tests, run by the suite (they live beside the scripts so the skill folder stays whole)."""
import os, shutil, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "claude-home", "skills", "watch-reels", "scripts"))
import test_breakdown as TB, test_post_batch as TP  # noqa: E402

# Subclasses, so each test id names this module and fast.py can rerun it from tests/.
needs_ffmpeg = unittest.skipUnless(shutil.which("ffmpeg"), "needs ffmpeg")


@needs_ffmpeg
class Breakdown(TB.T): pass


class Slides(TP.Slides): pass


class Batch(TP.Batch): pass


@needs_ffmpeg
class Page(TP.Page): pass


class Fetch(TP.Fetch): pass


class Offers(TP.Offers): pass
