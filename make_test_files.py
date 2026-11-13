"""Generates harmless dummy test files into test_files/."""
import os, zlib, struct
from PIL import Image
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_files"); os.makedirs(D, exist_ok=True)
w = lambda n, b: open(os.path.join(D, n), "wb").write(b)
w("sample.txt", b"This is a harmless sample text file for the file upload demo.\n")
w("sample.pdf", b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 100]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n")
Image.new("RGB", (64, 64), (20, 160, 120)).save(os.path.join(D, "sample.png"))
Image.new("RGB", (64, 64), (30, 100, 200)).save(os.path.join(D, "sample.jpg"))
w("fake_program.exe", b"HARMLESS DEMO: this is plain text pretending to be an .exe file. It cannot run.\n")
w("mismatch.png", b"I am plain text, not a real PNG image.\n")
w("invalid_type.csv", b"a,b,c\n1,2,3\n")
print("Test files created in", D)
