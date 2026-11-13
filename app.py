"""
Unrestricted File Upload Attack - Cyber Security ABA demonstration.

Two upload modules:
  /api/vulnerable/*  -> deliberately weak (no type validation)
  /api/secure/*      -> layered validation

SAFETY: uploaded files are NEVER executed, imported or served inline.
They are only written to disk as inert bytes and can only be downloaded
as 'application/octet-stream' attachments.
"""
import json, os, re, threading, time, uuid
from datetime import datetime
from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

BASE = os.path.dirname(os.path.abspath(__file__))
UPLOAD_ROOT = os.path.join(BASE, "uploads")
DIRS = {"vulnerable": os.path.join(UPLOAD_ROOT, "vulnerable"),
        "secure": os.path.join(UPLOAD_ROOT, "secure")}
for d in DIRS.values():
    os.makedirs(d, exist_ok=True)

MAX_SECURE_BYTES = 5 * 1024 * 1024          # secure module limit: 5 MB
HARD_REQUEST_LIMIT = 25 * 1024 * 1024       # keeps the demo machine safe

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = HARD_REQUEST_LIMIT
lock = threading.Lock()

# ---- allowlist: extension -> (allowed declared MIME types) -------------------
ALLOWED = {
    "pdf": {"application/pdf"},
    "txt": {"text/plain"},
    "jpg": {"image/jpeg"},
    "jpeg": {"image/jpeg"},
    "png": {"image/png"},
}


# ---- tiny JSON metadata store (no database needed) ---------------------------
def _index_path(mode): return os.path.join(DIRS[mode], "index.json")

def load_index(mode):
    try:
        with open(_index_path(mode)) as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): return []

def save_index(mode, rows):
    with open(_index_path(mode), "w") as f: json.dump(rows, f, indent=1)

def record(mode, row):
    with lock:
        rows = load_index(mode); rows.insert(0, row); save_index(mode, rows)

def now(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---- secure-module validators ------------------------------------------------
def magic_matches(ext, head):
    """Check real file content (signature), not the name."""
    if ext == "pdf":  return head.startswith(b"%PDF-")
    if ext == "png":  return head.startswith(b"\x89PNG\r\n\x1a\n")
    if ext in ("jpg", "jpeg"): return head.startswith(b"\xff\xd8\xff")
    if ext == "txt":  # text must be NUL-free and decodable
        if b"\x00" in head: return False
        try: head.decode("utf-8"); return True
        except UnicodeDecodeError:
            try: head[:-3].decode("utf-8"); return True   # cut multibyte char at boundary
            except UnicodeDecodeError: return False
    return False

def validate_secure(file, raw_name):
    """Return (ok, message, checks). Every layer must pass."""
    checks = []
    def step(name, passed, detail):
        checks.append({"check": name, "passed": passed, "detail": detail}); return passed

    # 1. Path traversal / suspicious filename
    bad = (".." in raw_name) or ("/" in raw_name) or ("\\" in raw_name) or ("\x00" in raw_name)
    if not step("Path traversal check", not bad, "Filename contains ../ or path separators" if bad else "Clean filename"):
        return False, "Rejected: filename contains path-traversal characters.", checks
    safe = secure_filename(raw_name)
    if not step("Filename sanitisation", bool(safe), "Sanitised to '%s'" % safe if safe else "Nothing usable left"):
        return False, "Rejected: invalid filename.", checks

    # 2. Extension allowlist
    ext = safe.rsplit(".", 1)[-1].lower() if "." in safe else ""
    if not step("Extension allowlist", ext in ALLOWED, ".%s %s" % (ext, "is allowed" if ext in ALLOWED else "is NOT in allowlist (pdf, txt, jpg, png)")):
        return False, "Rejected: '.%s' files are not allowed. Only PDF, TXT, JPG, PNG." % (ext or "?"), checks

    # 3. Declared MIME type
    mime = (file.mimetype or "").lower()
    if not step("MIME-type validation", mime in ALLOWED[ext], "Browser declared '%s'" % mime):
        return False, "Rejected: MIME type '%s' does not match a .%s file." % (mime, ext), checks

    # 4. Size (read in chunks, never trust Content-Length alone)
    size = 0; head = b""
    while True:
        chunk = file.stream.read(64 * 1024)
        if not chunk: break
        if size == 0: head = chunk[:2048]
        size += len(chunk)
        if size > MAX_SECURE_BYTES: break
    file.stream.seek(0)
    if not step("File-size limit (5 MB)", 0 < size <= MAX_SECURE_BYTES, "File too large or empty" if not (0 < size <= MAX_SECURE_BYTES) else "%d bytes" % size):
        return False, "Rejected: file is empty or larger than 5 MB.", checks

    # 5. Magic bytes
    if not step("File signature (magic bytes)", magic_matches(ext, head), "Real content %s a genuine .%s file" % ("matches" if magic_matches(ext, head) else "does NOT match", ext)):
        return False, "Rejected: file content does not match its .%s extension." % ext, checks
    return True, "ok", checks


# ---- routes ------------------------------------------------------------------
@app.route("/")
def index(): return render_template("index.html", max_mb=MAX_SECURE_BYTES // (1024 * 1024))

@app.after_request
def headers(r):
    r.headers["X-Content-Type-Options"] = "nosniff"
    return r

@app.errorhandler(413)
def too_big(_):
    return jsonify(accepted=False, message="Rejected: request exceeds the server hard limit (25 MB).", checks=[]), 413

@app.route("/api/<mode>/upload", methods=["POST"])
def upload(mode):
    if mode not in DIRS: return jsonify(error="unknown module"), 404
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify(accepted=False, message="No file selected.", checks=[]), 400
    raw_name = f.filename

    if mode == "vulnerable":
        # !!! INTENTIONALLY VULNERABLE: no extension, MIME, signature or size checks,
        # and the client's filename is trusted. Demo containment: only the final path
        # component is used so nothing can escape the sandbox folder, and the file is
        # stored as inert bytes - it is never executed or served inline.
        stored = os.path.basename(raw_name.replace("\\", "/")) or "unnamed"
        path = os.path.join(DIRS["vulnerable"], stored)
        f.save(path)
        size = os.path.getsize(path)
        record("vulnerable", {"id": stored, "name": raw_name, "stored_as": stored, "size": size,
                              "time": now(), "status": "Accepted", "type": f.mimetype})
        note = ""
        if ".." in raw_name or "/" in raw_name or "\\" in raw_name:
            note = " Path-traversal characters were NOT detected (sandbox kept the file inside the demo folder)."
        return jsonify(accepted=True, message="Upload successful: '%s' accepted without any validation.%s" % (raw_name, note),
                       checks=[{"check": "Any validation", "passed": False, "detail": "None performed (vulnerable by design)"}])

    ok, msg, checks = validate_secure(f, raw_name)
    if not ok:
        record("secure", {"id": uuid.uuid4().hex, "name": raw_name, "stored_as": "-", "size": 0,
                          "time": now(), "status": "Rejected", "type": f.mimetype})
        return jsonify(accepted=False, message=msg, checks=checks), 200
    ext = secure_filename(raw_name).rsplit(".", 1)[-1].lower()
    stored = uuid.uuid4().hex + "." + ext
    f.save(os.path.join(DIRS["secure"], stored))
    size = os.path.getsize(os.path.join(DIRS["secure"], stored))
    record("secure", {"id": stored, "name": secure_filename(raw_name), "stored_as": stored, "size": size,
                      "time": now(), "status": "Accepted", "type": f.mimetype})
    return jsonify(accepted=True, message="Upload successful: passed all 5 security checks. Stored as %s" % stored, checks=checks)

@app.route("/api/<mode>/files")
def files(mode):
    if mode not in DIRS: return jsonify(error="unknown module"), 404
    return jsonify(load_index(mode))

@app.route("/api/<mode>/download/<name>")
def download(mode, name):
    """Files are only ever offered as a forced download of raw bytes - never rendered or run."""
    if mode not in DIRS: return jsonify(error="unknown module"), 404
    if not any(r["stored_as"] == name for r in load_index(mode)):
        return jsonify(error="not found"), 404
    return send_from_directory(DIRS[mode], name, as_attachment=True, mimetype="application/octet-stream")

@app.route("/api/<mode>/clear", methods=["POST"])
def clear(mode):
    if mode not in DIRS: return jsonify(error="unknown module"), 404
    with lock:
        for n in os.listdir(DIRS[mode]):
            if n != ".gitkeep":
                p = os.path.join(DIRS[mode], n)
                if os.path.isfile(p): os.remove(p)
    return jsonify(ok=True)

if __name__ == "__main__":
    print("Unrestricted File Upload demo -> http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)   # localhost only, debug off
