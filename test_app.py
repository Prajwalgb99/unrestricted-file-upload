"""Automated tests for all 9 required cases. Run:  python test_app.py"""
import io, os, unittest
import app as A

T = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_files")
def rd(n): return open(os.path.join(T, n), "rb").read()

class Upload(unittest.TestCase):
    @classmethod
    def setUpClass(c): c.c = A.app.test_client()
    def setUp(self):
        for m in ("vulnerable", "secure"): self.c.post("/api/%s/clear" % m)
    def up(self, mode, name, data, mime):
        r = self.c.post("/api/%s/upload" % mode, data={"file": (io.BytesIO(data), name, mime)}, content_type="multipart/form-data")
        return r.get_json()

    def test1_pdf(self):
        self.assertTrue(self.up("secure", "sample.pdf", rd("sample.pdf"), "application/pdf")["accepted"])
    def test2_txt(self):
        self.assertTrue(self.up("secure", "sample.txt", rd("sample.txt"), "text/plain")["accepted"])
    def test3_jpg(self):
        self.assertTrue(self.up("secure", "sample.jpg", rd("sample.jpg"), "image/jpeg")["accepted"])
    def test4_png(self):
        self.assertTrue(self.up("secure", "sample.png", rd("sample.png"), "image/png")["accepted"])
    def test5_renamed_exe(self):
        d = rd("fake_program.exe")
        self.assertTrue(self.up("vulnerable", "fake_program.exe", d, "application/x-msdownload")["accepted"])
        r = self.up("secure", "fake_program.exe", d, "application/x-msdownload")
        self.assertFalse(r["accepted"]); self.assertIn("not allowed", r["message"])
    def test6_oversized(self):
        big = b"%PDF-" + b"A" * (6 * 1024 * 1024)
        self.assertTrue(self.up("vulnerable", "big.pdf", big, "application/pdf")["accepted"])
        r = self.up("secure", "big.pdf", big, "application/pdf")
        self.assertFalse(r["accepted"]); self.assertIn("5 MB", r["message"])
    def test7_invalid_type(self):
        r = self.up("secure", "invalid_type.csv", rd("invalid_type.csv"), "text/csv")
        self.assertFalse(r["accepted"])
    def test8_path_traversal(self):
        r = self.up("secure", "../../evil.txt", b"harmless", "text/plain")
        self.assertFalse(r["accepted"]); self.assertIn("path-traversal", r["message"])
        v = self.up("vulnerable", "../../evil.txt", b"harmless", "text/plain")
        self.assertTrue(v["accepted"])
        self.assertFalse(os.path.exists(os.path.join(A.BASE, "..", "evil.txt")))   # sandbox held
    def test9_mismatch(self):
        r = self.up("secure", "mismatch.png", rd("mismatch.png"), "image/png")
        self.assertFalse(r["accepted"]); self.assertIn("does not match", r["message"])
    def test_secure_random_name(self):
        r = self.up("secure", "sample.txt", rd("sample.txt"), "text/plain")
        self.assertIn("Stored as", r["message"]); self.assertNotIn("sample", r["message"].split("Stored as")[1])
    def test_download_is_attachment(self):
        self.up("vulnerable", "fake_program.exe", rd("fake_program.exe"), "x")
        r = self.c.get("/api/vulnerable/download/fake_program.exe")
        self.assertIn("attachment", r.headers["Content-Disposition"])
        self.assertEqual(r.mimetype, "application/octet-stream")

if __name__ == "__main__":
    unittest.main(verbosity=2)
