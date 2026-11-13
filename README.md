# Unrestricted File Upload Attack: Cyber Security ABA Demonstration

**Subtitle:** Understanding Web Application File Upload Vulnerabilities

A Flask web application that shows, side by side, an **insecure** file-upload system and a **secure** one. Everything is harmless: only dummy files are used, and uploaded files are **never executed**.

---

## 1. What the project contains

```
unrestricted-file-upload/
├── app.py                 Flask backend: vulnerable + secure upload logic
├── requirements.txt       Python dependency (Flask)
├── README.md              This file
├── make_test_files.py     Generates harmless dummy test files (needs Pillow, optional)
├── test_app.py            Automated tests for all 9 required test cases
├── uploads/
│   ├── vulnerable/        Files saved by the insecure module (inert, never run)
│   └── secure/            Files saved by the secure module (random names)
├── templates/index.html   Dashboard, demo mode, theory sections
├── static/css/style.css   Dark navy / green / blue theme
├── static/js/script.js    Upload progress, file lists, automated demo
└── test_files/            sample.txt, sample.pdf, sample.png, sample.jpg,
                           fake_program.exe (text), mismatch.png (text), invalid_type.csv
```

**Technology stack:** Python 3 · Flask · HTML5 · CSS3 · JavaScript · local JSON metadata files (no database).

---

## 2. How to run

1. Install Python 3.9+ from python.org.
2. Open a terminal inside the project folder.
3. (Recommended) create a virtual environment:
   - Windows: `python -m venv venv` then `venv\Scripts\activate`
   - Linux/macOS: `python3 -m venv venv` then `source venv/bin/activate`
4. Install the dependency: `pip install -r requirements.txt`
5. Start the server: `python app.py`
6. Open **http://127.0.0.1:5000** in your browser.

Run the automated tests: `python test_app.py` (expected: `Ran 11 tests ... OK`).
If you want to regenerate the test files: `pip install pillow` then `python make_test_files.py`.

---

## 3. How to demonstrate (about 5 minutes)

### Option A: one click
1. Scroll to **Attack Demonstration Mode** and click **Run Automated Demo**.
2. Watch the 6 steps light up. The left card shows the vulnerable result, the right card the secure result.
3. Read the Step 6 explanation aloud.

### Option B: manual, using the two cards
| Step | Action | Expected result |
|---|---|---|
| 1 | Vulnerable card: upload `test_files/sample.pdf` | **Accepted** |
| 2 | Vulnerable card: upload `test_files/fake_program.exe` | **Accepted** (no validation) |
| 3 | Point out the fake .exe now sits in the file list | Vulnerability shown |
| 4 | Secure card: upload `fake_program.exe` | **Rejected**: ".exe files are not allowed" |
| 5 | Secure card: upload `mismatch.png` (text inside) | **Rejected**: content does not match .png |
| 6 | Secure card: upload `sample.pdf`, `sample.png` | **Accepted**, stored with a random name |

### Expected results for all test cases
| # | Case | Vulnerable | Secure |
|---|---|---|---|
| 1 | Normal PDF | Accepted | Accepted |
| 2 | Normal TXT | Accepted | Accepted |
| 3 | Normal JPG | Accepted | Accepted |
| 4 | Normal PNG | Accepted | Accepted |
| 5 | TXT renamed `.exe` | **Accepted** | **Rejected** (extension not allowed) |
| 6 | File larger than 5 MB | **Accepted** | **Rejected** (size limit) |
| 7 | Invalid type (`.csv`) | **Accepted** | **Rejected** (allowlist) |
| 8 | Filename `../../evil.txt` | **Accepted**, traversal not detected | **Rejected** (path traversal) |
| 9 | Text content named `.png` | **Accepted** | **Rejected** (magic bytes mismatch) |

---

## 4. Presentation script for faculty (simple explanation)

> "Websites often let users upload files, such as profile photos or documents. If the website does not check what is really being uploaded, an attacker can upload a dangerous file disguised as a harmless one. This is called an **Unrestricted File Upload** vulnerability.
>
> My project has two upload pages. The **vulnerable** one accepts anything, so a text file renamed to `.exe` goes straight through. The **secure** one runs five checks: filename safety, extension allowlist, MIME type, file size, and the real file signature (magic bytes). The same fake `.exe` is rejected.
>
> The key lesson: **a file extension is only a name that the user controls. A secure system must verify the actual content.** For safety, all files here are harmless and are never executed."

### What is an Unrestricted File Upload Attack?
The server accepts uploaded files without properly validating name, type, content or size.

### How does it work?
Attacker uploads a malicious file disguised as an allowed type. If the server stores it in a place where it can be run, or serves it to other users, the attacker gains control or spreads malware.

### Why is it dangerous / real-world implications?
Remote code execution, server takeover, malware distribution, stored XSS, data theft, denial of service by huge files, overwriting of critical files.

### Common causes
Trusting extensions, trusting browser-supplied MIME types, no size limit, using the user's filename on disk, uploads stored inside a web-executable folder.

---

## 5. Security measures implemented

**Secure module (`/api/secure/upload`):**
1. **Path-traversal rejection**: names containing `..`, `/`, `\` or NUL are refused.
2. **Filename sanitising** with `werkzeug.utils.secure_filename`.
3. **Extension allowlist**: only PDF, TXT, JPG/JPEG, PNG.
4. **MIME-type validation**: declared type must match the extension.
5. **Size limit**: 5 MB, enforced while reading the stream.
6. **Magic-byte validation**: PDF `%PDF-`, PNG `89 50 4E 47...`, JPEG `FF D8 FF`; TXT must be NUL-free valid UTF-8.
7. **Random server-side names** (UUID), so the user cannot choose the stored name.
8. **Safe storage**: `uploads/` is outside Flask's `static/` folder and is not directly URL-accessible.
9. **Forced download**: files are offered only as `application/octet-stream` attachments with `X-Content-Type-Options: nosniff`.

**Demo safety (both modules):** files are never executed, imported or rendered; the server binds to `127.0.0.1` only with debug off; the vulnerable module keeps only the final path component so nothing can escape the demo folder; a 25 MB hard request cap protects your machine. No malware, web shells or reverse shells exist in this project.

---

## 6. Viva questions and answers

1. **What is an unrestricted file upload vulnerability?** A flaw where a web app accepts uploaded files without validating their type, content, name or size, letting attackers upload harmful files.
2. **Why is it dangerous?** It can lead to remote code execution, malware hosting, stored XSS, defacement, data theft and denial of service.
3. **Why is checking only the extension not enough?** The extension is just part of the filename and is fully user-controlled. `malware.exe` can be renamed `photo.png`.
4. **What are magic bytes?** The first bytes of a file that identify its real format, e.g. `%PDF-` for PDFs, `FF D8 FF` for JPEG.
5. **Why not trust the MIME type sent by the browser?** It comes from the client's request header and can be forged, so it is only one layer, not proof.
6. **What is an allowlist and why is it better than a blocklist?** An allowlist permits only known-good types. A blocklist misses new or unusual dangerous types (e.g. `.phtml`, double extensions).
7. **Why rename uploaded files with random names?** It stops overwriting, guessing, path tricks and attacker-chosen names or extensions.
8. **What is path traversal?** Using `../` in a filename to write outside the intended folder, e.g. to overwrite application files.
9. **Why limit file size?** To prevent denial of service from disk or memory exhaustion by huge uploads.
10. **Why store uploads outside the web root / static folder?** So uploaded files cannot be requested and executed or rendered directly by the web server.
11. **What does `X-Content-Type-Options: nosniff` do?** It tells browsers not to guess a file's type, which blocks content-type confusion attacks.
12. **What does the `Content-Disposition: attachment` header do?** It forces a download instead of letting the browser display or run the content.
13. **How does your secure module detect a text file renamed to .png?** The magic-byte check fails: the content does not start with the PNG signature.
14. **What would you add for production?** Antivirus scanning, image re-encoding, authentication, rate limiting, storing files in object storage with no execute permission, and logging.
15. **Is validating on the client side (JavaScript) enough?** No. Client checks are for convenience; attackers bypass the browser, so the server must validate.
16. **What is a double-extension attack?** A name like `shell.php.jpg` that fools weak filters. Allowlisting the final extension plus content checks defends against it.
17. **Which OWASP area does this belong to?** File upload weaknesses fall under insecure design and security misconfiguration in OWASP guidance; OWASP publishes a File Upload Cheat Sheet.
18. **Why is your vulnerable module still safe to run?** Files are stored as inert bytes in an isolated folder, never executed or rendered, only downloadable as raw attachments, and the server listens on localhost only.
19. **What is defense in depth?** Using several independent protections so that if one fails, others still stop the attack. The secure module uses five validation layers plus safe storage.
20. **How can an attacker use an uploaded image for XSS?** By embedding script in SVG/HTML-like content or abusing content sniffing. That is why only PNG/JPG/PDF/TXT are allowed and `nosniff` is set.

---

## 7. Troubleshooting
- **`ModuleNotFoundError: flask`**: run `pip install -r requirements.txt`.
- **Port 5000 busy** (e.g. macOS AirPlay): change `port=5000` in the last line of `app.py`.
- **Reset everything**: click *Reset* in the demo section or *Reset folder* on each card.

*Educational use only. Do not deploy the vulnerable module on a public server.*
