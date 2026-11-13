const $ = (s, r = document) => r.querySelector(s);
const fmt = b => b < 1024 ? b + " B" : b < 1048576 ? (b / 1024).toFixed(1) + " KB" : (b / 1048576).toFixed(2) + " MB";
const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function sendFile(mode, file, onProgress) {
  return new Promise(res => {
    const x = new XMLHttpRequest(), fd = new FormData();
    fd.append("file", file, file.name);
    x.open("POST", `/api/${mode}/upload`);
    x.upload.onprogress = e => e.lengthComputable && onProgress && onProgress(e.loaded / e.total * 100);
    x.onload = () => { try { res(JSON.parse(x.responseText)); } catch { res({ accepted: false, message: "Server error", checks: [] }); } };
    x.onerror = () => res({ accepted: false, message: "Network error", checks: [] });
    x.send(fd);
  });
}

async function loadFiles(mode, card) {
  const rows = await (await fetch(`/api/${mode}/files`)).json();
  $(".rows", card).innerHTML = rows.length ? rows.map(r => `<tr>
    <td>${esc(r.name)}</td><td>${fmt(r.size)}</td><td>${r.time}</td>
    <td><span class="tag ${r.status}">${r.status}</span></td>
    <td>${r.status === "Accepted" ? `<a class="dl" href="/api/${mode}/download/${encodeURIComponent(r.stored_as)}">download</a>` : ""}</td></tr>`).join("")
    : `<tr><td colspan="5" class="muted">No files yet</td></tr>`;
}

function showResult(card, r) {
  const m = $(".msg", card); m.textContent = r.message; m.className = "msg " + (r.accepted ? "ok" : "no");
  $(".checks", card).innerHTML = (r.checks || []).map(c => `<li class="${c.passed ? "p" : "f"}"><b>${esc(c.check)}:</b> ${esc(c.detail)}</li>`).join("");
}

document.querySelectorAll(".card[data-mode]").forEach(card => {
  const mode = card.dataset.mode, input = $(".file-input", card);
  input.onchange = () => $(".drop-text", card).textContent = input.files[0] ? input.files[0].name : "Click to choose a file";
  $(".upload-btn", card).onclick = async () => {
    if (!input.files[0]) { showResult(card, { accepted: false, message: "Please choose a file first.", checks: [] }); return; }
    const bar = $(".bar-fill", card); bar.style.width = "0";
    const r = await sendFile(mode, input.files[0], p => bar.style.width = p + "%");
    bar.style.width = "100%"; showResult(card, r); loadFiles(mode, card);
  };
  $(".clear-btn", card).onclick = async () => { await fetch(`/api/${mode}/clear`, { method: "POST" }); showResult(card, { accepted: true, message: "Folder reset.", checks: [] }); loadFiles(mode, card); };
  const traversalBtn = $(".traversal-btn", card);
  if (traversalBtn) {
    traversalBtn.onclick = async () => {
      const dummyFile = new File(["harmless test content for path traversal demonstration\n"], "../../evil.txt", { type: "text/plain" });
      const bar = $(".bar-fill", card); bar.style.width = "0";
      const r = await sendFile(mode, dummyFile, p => bar.style.width = p + "%");
      bar.style.width = "100%"; showResult(card, r); loadFiles(mode, card);
    };
  }
  loadFiles(mode, card);
});

// ---------- Attack demonstration ----------
const sleep = ms => new Promise(r => setTimeout(r, ms));
const steps = [...document.querySelectorAll(".step")];
const mark = (n, s) => steps[n - 1].className = "step " + s;
const reload = () => document.querySelectorAll(".card[data-mode]").forEach(c => loadFiles(c.dataset.mode, c));

async function runDemo() {
  const btn = $("#runDemo"); btn.disabled = true;
  steps.forEach(s => s.className = "step"); $("#step6").hidden = true;
  $("#resV").innerHTML = $("#resS").innerHTML = "Running…";
  const pdf = new File(["%PDF-1.4\n% harmless dummy PDF\n%%EOF\n"], "normal.pdf", { type: "application/pdf" });
  const exe = new File(["HARMLESS DEMO: plain text pretending to be an .exe. It cannot run.\n"], "fake_program.exe", { type: "application/x-msdownload" });
  const block = (n, r) => `<p><b>${n}</b><br><span class="tag ${r.accepted ? "Accepted" : "Rejected"}">${r.accepted ? "Accepted" : "Rejected"}</span> ${esc(r.message)}</p>`;

  mark(1, "active"); const a = await sendFile("vulnerable", pdf); $("#resV").innerHTML = block("normal.pdf", a); mark(1, "done"); await sleep(700);
  mark(2, "active"); const b = await sendFile("vulnerable", exe); await sleep(500); mark(2, "done");
  mark(3, "active"); $("#resV").innerHTML += block("fake_program.exe", b) + `<p class="muted">⚠ The fake .exe was accepted: the server never looked at the real content.</p>`; await sleep(900); mark(3, "done");
  mark(4, "active"); const c = await sendFile("secure", exe); await sleep(700); mark(4, "done");
  mark(5, "active");
  $("#resS").innerHTML = block("fake_program.exe", c) + `<ul>${(c.checks || []).map(k => `<li>${k.passed ? "✓" : "✗"} ${esc(k.check)}: ${esc(k.detail)}</li>`).join("")}</ul>`;
  await sleep(900); mark(5, "done");
  mark(6, "active"); $("#step6").hidden = false; await sleep(400); mark(6, "done");
  reload(); btn.disabled = false;
}
$("#runDemo").onclick = runDemo;
$("#resetDemo").onclick = async () => {
  await Promise.all(["vulnerable", "secure"].map(m => fetch(`/api/${m}/clear`, { method: "POST" })));
  steps.forEach(s => s.className = "step"); $("#step6").hidden = true;
  $("#resV").textContent = $("#resS").textContent = "Run the demo to see the result."; reload();
};
