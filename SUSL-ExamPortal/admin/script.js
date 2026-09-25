"use strict";
/* ExamPortal — Administrator interface.
   Front-end only: data is sample data persisted in this browser (localStorage).
   Replace the load()/save() pair with API calls when an admin backend exists. */

const session = SUSLSession.require("admin");
const $ = id => document.getElementById(id);
const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const STORE = "susl_admin_data_v1";
const minsAgo = m => Date.now() - m * 60000;

/* ---------- sample data ---------- */
const seed = () => ({
  exams: [
    { name: "Software Engineering - Mid Term", course: "CS205", date: "2026-09-25", duration: "90 minutes", students: 124, status: "Scheduled" },
    { name: "Database Management Systems", course: "CS204", date: "2026-09-28", duration: "120 minutes", students: 118, status: "Live" },
    { name: "Operating Systems - Final", course: "CS206", date: "2026-10-02", duration: "120 minutes", students: 125, status: "Completed" },
    { name: "Computer Networks", course: "CS207", date: "2026-10-07", duration: "90 minutes", students: 106, status: "Scheduled" },
    { name: "Information Systems", course: "IS210", date: "2026-10-10", duration: "60 minutes", students: 94, status: "Scheduled" }
  ],
  students: [
    { name: "Nethmi Perera", reg: "SUSL/CS/24/001", email: "nethmi@std.sab.ac.lk", program: "Computer Science", year: "2", status: "Active" },
    { name: "Kavindu Silva", reg: "SUSL/CS/24/018", email: "kavindu@std.sab.ac.lk", program: "Computer Science", year: "2", status: "Active" },
    { name: "Tharushi Fernando", reg: "SUSL/IT/23/042", email: "tharushi@std.sab.ac.lk", program: "Information Technology", year: "3", status: "Active" },
    { name: "Sahan Wijesinghe", reg: "SUSL/CS/25/081", email: "sahan@std.sab.ac.lk", program: "Computer Science", year: "1", status: "Active" },
    { name: "Dilki Senanayake", reg: "SUSL/IT/24/055", email: "dilki@std.sab.ac.lk", program: "Information Technology", year: "2", status: "Suspended" }
  ],
  lecturers: [
    { name: "Dr. A. Perera", email: "aperera@sab.ac.lk", dept: "Computing", courses: "4", status: "Active" },
    { name: "Ms. N. Fernando", email: "nfernando@sab.ac.lk", dept: "Computing", courses: "3", status: "Active" },
    { name: "Mr. K. Jayasinghe", email: "kjayasinghe@sab.ac.lk", dept: "Information Systems", courses: "5", status: "Active" },
    { name: "Dr. S. Bandara", email: "sbandara@sab.ac.lk", dept: "Computing", courses: "4", status: "Active" }
  ],
  questions: [
    { id: "Q00186", text: "What is the primary purpose of an operating system?", course: "Operating Systems", type: "Multiple Choice", marks: 2 },
    { id: "Q00185", text: "Explain the difference between primary and foreign keys.", course: "Database Systems", type: "Short Answer", marks: 5 },
    { id: "Q00184", text: "Which software development model uses iterative development?", course: "Software Engineering", type: "Multiple Choice", marks: 2 }
  ],
  results: [
    { exam: "Database Systems - Mid Term", course: "CS204", submitted: 112, graded: 112, status: "Published" },
    { exam: "Software Engineering - Quiz 02", course: "CS205", submitted: 98, graded: 86, status: "Pending" },
    { exam: "Operating Systems - Final", course: "CS206", submitted: 125, graded: 125, status: "Published" }
  ],
  activity: [
    { c: "blue", title: "New exam created", text: "Software Engineering - Year 2", ts: minsAgo(12) },
    { c: "cyan", title: "Student account added", text: "Registration: SUSL/CS/24/081", ts: minsAgo(35) },
    { c: "purple", title: "Results published", text: "Database Management Systems", ts: minsAgo(60) },
    { c: "orange", title: "Question bank updated", text: "25 new questions added", ts: minsAgo(120) }
  ],
  settings: { uni: "Sabaragamuwa University of Sri Lanka", sys: "ExamPortal", mail: "support@sab.ac.lk", duration: "60 minutes", auto: true, approve: true },
  nextQ: 187
});
// Institution-wide totals the sample rows don't cover; displayed totals = base + rows in the tables.
const BASE = { exams: 19, students: 1243, completed: 17, pending: 5, q: 1861, mcq: 1418, written: 443 };

let db = load();
function load() { try { const r = localStorage.getItem(STORE); if (r) return JSON.parse(r); } catch (e) {} return seed(); }
function save() { try { localStorage.setItem(STORE, JSON.stringify(db)); } catch (e) {} }
function log(c, title, text) { db.activity.unshift({ c, title, text, ts: Date.now() }); db.activity = db.activity.slice(0, 8); }

/* ---------- helpers ---------- */
const fmtDate = iso => { const d = new Date(iso + "T00:00:00"); return isNaN(d) ? esc(iso) : d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" }); };
const badge = s => `<span class="badge ${esc(String(s).toLowerCase())}">${esc(s)}</span>`;
const has = (o, q) => Object.values(o).join(" ").toLowerCase().includes(q.toLowerCase());
function ago(ts) { const m = Math.max(1, Math.round((Date.now() - ts) / 60000)); return m < 60 ? m + " minute" + (m > 1 ? "s" : "") + " ago" : m < 1440 ? Math.round(m / 60) + " hour" + (Math.round(m / 60) > 1 ? "s" : "") + " ago" : Math.round(m / 1440) + " day(s) ago"; }
function toast(msg) { const t = $("toast"); t.textContent = msg; t.classList.add("show"); clearTimeout(window.toastTimer); window.toastTimer = setTimeout(() => t.classList.remove("show"), 2600); }
function download(name, rows) {
  const csv = rows.map(r => r.map(v => '"' + String(v == null ? "" : v).replace(/"/g, '""') + '"').join(",")).join("\r\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" }));
  a.download = name; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}
const more = (kind, i) => `<button class="more" data-menu="${kind}" data-i="${i}" aria-label="Row actions" aria-haspopup="menu">•••</button>`;

/* ---------- navigation ---------- */
const TITLES = { dashboard: "Dashboard", exams: "Exams", questions: "Question Bank", students: "Students", lecturers: "Lecturers", results: "Results", reports: "Reports", settings: "Settings" };
const navItems = document.querySelectorAll(".nav-item");
function showPage(page) {
  Object.keys(TITLES).forEach(p => { const el = $(p + "Page"); if (el) el.classList.toggle("hidden", p !== page); });
  navItems.forEach(b => b.classList.toggle("active", b.dataset.page === page));
  $("pageTitle").textContent = TITLES[page];
  $("sidebar").classList.remove("open");
  window.scrollTo({ top: 0, behavior: "smooth" });
}
navItems.forEach(b => b.addEventListener("click", () => showPage(b.dataset.page)));
document.querySelectorAll("[data-page-link]").forEach(b => b.addEventListener("click", () => showPage(b.dataset.pageLink)));
$("menuBtn").onclick = () => $("sidebar").classList.toggle("open");

/* ---------- rendering ---------- */
const q = id => ($(id) ? $(id).value.trim() : "");
function render() {
  const eq = q("examSearch"), es = $("examStatus").value;
  const exams = db.exams.map((e, i) => ({ e, i })).filter(({ e }) => (!eq || has(e, eq)) && (es === "All Status" || e.status === es));
  $("examTable").innerHTML = exams.map(({ e, i }) => `<tr><td>${esc(e.name)}</td><td>${esc(e.course)}</td><td>${fmtDate(e.date)}</td><td>${esc(e.students)}</td><td>${badge(e.status)}</td><td>${more("exams", i)}</td></tr>`).join("") || empty(6, "No examinations match your filters.");
  $("recentExams").innerHTML = db.exams.slice(0, 4).map((e, i) => `<tr><td>${esc(e.name)}</td><td>${fmtDate(e.date)}</td><td>${esc(e.students)}</td><td>${badge(e.status)}</td><td>${more("exams", i)}</td></tr>`).join("");

  const sq = q("studentSearch"), sp = $("studentProgram").value;
  $("studentTable").innerHTML = db.students.map((s, i) => ({ s, i })).filter(({ s }) => (!sq || has(s, sq)) && (sp === "All Programs" || s.program === sp))
    .map(({ s, i }) => `<tr><td>${esc(s.name)}</td><td>${esc(s.reg)}</td><td>${esc(s.program)}</td><td>${esc(s.year)}</td><td>${badge(s.status)}</td><td>${more("students", i)}</td></tr>`).join("") || empty(6, "No students match your filters.");

  const lq = q("lecturerSearch");
  $("lecturerTable").innerHTML = db.lecturers.map((l, i) => ({ l, i })).filter(({ l }) => !lq || has(l, lq))
    .map(({ l, i }) => `<tr><td>${esc(l.name)}</td><td>${esc(l.email)}</td><td>${esc(l.dept)}</td><td>${esc(l.courses)}</td><td>${badge(l.status)}</td><td>${more("lecturers", i)}</td></tr>`).join("") || empty(6, "No lecturers found.");

  const qq = q("questionSearch");
  $("questionList").innerHTML = db.questions.map((x, i) => ({ x, i })).filter(({ x }) => !qq || has(x, qq))
    .map(({ x, i }) => `<div class="question-row"><b>${esc(x.id)}</b><span>${esc(x.text)}</span><em>${esc(x.course)}</em>${more("questions", i)}</div>`).join("") || `<p class="empty">No questions found.</p>`;

  const rq = q("resultSearch"), rf = $("resultFilter").value;
  $("resultTable").innerHTML = db.results.map((r, i) => ({ r, i })).filter(({ r }) => (!rq || has(r, rq)) && (rf === "All Results" || r.status === rf))
    .map(({ r, i }) => `<tr><td>${esc(r.exam)}</td><td>${esc(r.course)}</td><td>${esc(r.submitted)}</td><td>${esc(r.graded)}</td><td>${badge(r.status)}</td><td>${more("results", i)}</td></tr>`).join("") || empty(6, "No results match your filters.");

  const n = f => db.questions.filter(f).length;
  $("examCount").textContent = BASE.exams + db.exams.length;
  $("studentCount").textContent = (BASE.students + db.students.length).toLocaleString();
  $("completedCount").textContent = BASE.completed + db.exams.filter(e => e.status === "Completed").length;
  $("pendingCount").textContent = String(BASE.pending + db.results.filter(r => r.status === "Pending").length).padStart(2, "0");
  $("qTotal").textContent = (BASE.q + db.questions.length).toLocaleString();
  $("qMcq").textContent = (BASE.mcq + n(x => x.type === "Multiple Choice")).toLocaleString();
  $("qWritten").textContent = (BASE.written + n(x => x.type !== "Multiple Choice")).toLocaleString();

  $("activityList").innerHTML = db.activity.map(a => `<div class="activity"><b class="dot ${esc(a.c)}-dot"></b><div><strong>${esc(a.title)}</strong><p>${esc(a.text)}</p><small>${ago(a.ts)}</small></div></div>`).join("");
  save();
}
const empty = (cols, msg) => `<tr><td colspan="${cols}" class="empty">${msg}</td></tr>`;
["examSearch", "studentSearch", "lecturerSearch", "questionSearch", "resultSearch"].forEach(id => $(id).addEventListener("input", render));
["examStatus", "studentProgram", "resultFilter"].forEach(id => $(id).addEventListener("change", render));

/* ---------- add / edit form ---------- */
const PROGRAMS = ["Computer Science", "Information Technology"];
const FORMS = {
  exam: { list: "exams", title: "Examination", fields: [
    { k: "name", label: "Examination Name", req: 1 },
    { k: "course", label: "Course Code", req: 1, pattern: "[A-Za-z]{2,4}[0-9]{3,4}", hint: "e.g. CS205" },
    { k: "date", label: "Examination Date", type: "date", req: 1 },
    { k: "duration", label: "Duration", type: "select", opts: ["60 minutes", "90 minutes", "120 minutes", "180 minutes"] },
    { k: "students", label: "Registered Students", type: "number", min: 0, def: 0 },
    { k: "status", label: "Status", type: "select", opts: ["Scheduled", "Live", "Completed"] } ] },
  student: { list: "students", title: "Student", fields: [
    { k: "name", label: "Full Name", req: 1 },
    { k: "reg", label: "Registration Number", req: 1, pattern: "SUSL/[A-Z]{2,3}/[0-9]{2}/[0-9]{3}", hint: "e.g. SUSL/CS/24/001" },
    { k: "email", label: "Email", type: "email", req: 1 },
    { k: "program", label: "Programme", type: "select", opts: PROGRAMS },
    { k: "year", label: "Academic Year", type: "select", opts: ["1", "2", "3", "4"] },
    { k: "status", label: "Status", type: "select", opts: ["Active", "Suspended"] } ] },
  lecturer: { list: "lecturers", title: "Lecturer", fields: [
    { k: "name", label: "Full Name", req: 1 },
    { k: "email", label: "Email", type: "email", req: 1 },
    { k: "dept", label: "Department", type: "select", opts: ["Computing", "Information Systems", "Physical Sciences & Technology"] },
    { k: "courses", label: "Assigned Courses", type: "number", min: 0, def: 1 },
    { k: "status", label: "Status", type: "select", opts: ["Active", "Suspended"] } ] },
  question: { list: "questions", title: "Question", fields: [
    { k: "text", label: "Question", type: "textarea", req: 1 },
    { k: "course", label: "Course", req: 1 },
    { k: "type", label: "Question Type", type: "select", opts: ["Multiple Choice", "True / False", "Short Answer", "Essay"] },
    { k: "marks", label: "Marks", type: "number", min: 1, def: 2, req: 1 } ] }
};
let editing = null; // { type, index }
const modal = $("modal");

function openModal(type, index) {
  const f = FORMS[type], rec = index != null ? db[f.list][index] : null;
  editing = { type, index: index != null ? index : null };
  $("modalTitle").textContent = (rec ? "Edit " : type === "exam" ? "Create " : "Add ") + f.title;
  $("modalSubtitle").textContent = rec ? "Update the details below." : "Enter the required details below.";
  $("modalFields").innerHTML = f.fields.map(x => {
    const v = rec ? rec[x.k] : (x.def != null ? x.def : "");
    const a = `id="f_${x.k}" name="${x.k}" ${x.req ? "required" : ""}`;
    let ctl;
    if (x.type === "select") ctl = `<select ${a}>${x.opts.map(o => `<option ${String(v) === o ? "selected" : ""}>${esc(o)}</option>`).join("")}</select>`;
    else if (x.type === "textarea") ctl = `<textarea ${a} rows="3">${esc(v)}</textarea>`;
    else ctl = `<input ${a} type="${x.type || "text"}" value="${esc(v)}" ${x.pattern ? `pattern="${x.pattern}" title="${esc(x.hint || "")}"` : ""} ${x.min != null ? `min="${x.min}"` : ""} placeholder="${esc(x.hint || "")}">`;
    return `<div class="field"><label for="f_${x.k}">${esc(x.label)}</label>${ctl}<small class="err" id="e_${x.k}"></small></div>`;
  }).join("");
  modal.classList.remove("hidden");
  const first = $("modalFields").querySelector("input,select,textarea"); if (first) first.focus();
}
function closeModal() { modal.classList.add("hidden"); editing = null; }
$("modalClose").onclick = closeModal;
modal.addEventListener("click", e => { if (e.target === modal) closeModal(); });

$("modalForm").addEventListener("submit", e => {
  e.preventDefault();
  const { type, index } = editing, f = FORMS[type], rec = {};
  let ok = true;
  f.fields.forEach(x => {
    const el = $("f_" + x.k), err = $("e_" + x.k); err.textContent = "";
    el.value = el.value.trim();
    if (x.k === "reg" || (x.k === "course" && type === "exam")) el.value = el.value.toUpperCase();
    if (!el.checkValidity()) { ok = false; err.textContent = el.validity.valueMissing ? "This field is required." : (x.hint ? "Use the format " + x.hint : "Enter a valid value."); }
    rec[x.k] = el.value;
  });
  if (!ok) return;
  const list = db[f.list];
  const dup = type === "student" ? list.some((s, i) => s.reg.toLowerCase() === rec.reg.toLowerCase() && i !== index)
    : type === "lecturer" ? list.some((l, i) => l.email.toLowerCase() === rec.email.toLowerCase() && i !== index) : false;
  if (dup) { $("e_" + (type === "student" ? "reg" : "email")).textContent = "This " + (type === "student" ? "registration number" : "email") + " already exists."; return; }
  if (type === "exam") rec.students = Number(rec.students) || 0;
  if (type === "question") rec.marks = Number(rec.marks);
  if (index != null) { Object.assign(list[index], rec); log("blue", f.title + " updated", rec.name || rec.text.slice(0, 50)); toast(f.title + " updated."); }
  else {
    if (type === "question") { rec.id = "Q" + String(db.nextQ++).padStart(5, "0"); list.unshift(rec); }
    else list.unshift(rec);
    log({ exam: "blue", student: "cyan", lecturer: "purple", question: "orange" }[type], { exam: "New exam created", student: "Student account added", lecturer: "Lecturer account added", question: "Question added" }[type], rec.name || rec.text.slice(0, 50));
    toast(f.title + " added successfully.");
  }
  closeModal(); render();
});

document.getElementById("createExamBtn").onclick = () => openModal("exam");
$("addExam").onclick = () => openModal("exam");
$("addStudent").onclick = () => openModal("student");
$("addLecturer").onclick = () => openModal("lecturer");
$("addQuestion").onclick = () => openModal("question");
document.querySelectorAll("[data-action]").forEach(b => b.onclick = () => b.dataset.action === "report" ? showPage("reports") : openModal(b.dataset.action));

/* ---------- row action menu ---------- */
const menu = $("rowMenu");
const MENUS = {
  exams: (e) => [["Edit", "edit"], ...["Scheduled", "Live", "Completed"].filter(s => s !== e.status).map(s => ["Mark as " + s, "status:" + s]), ["Delete", "delete", 1]],
  students: (s) => [["Edit", "edit"], [s.status === "Active" ? "Suspend" : "Activate", "toggle"], ["Delete", "delete", 1]],
  lecturers: (l) => [["Edit", "edit"], [l.status === "Active" ? "Suspend" : "Activate", "toggle"], ["Delete", "delete", 1]],
  questions: () => [["Edit", "edit"], ["Delete", "delete", 1]],
  results: (r) => [[r.status === "Pending" ? "Publish results" : "Withdraw to pending", "publish"]]
};
const SINGULAR = { exams: "exam", students: "student", lecturers: "lecturer", questions: "question" };
let menuCtx = null;
document.addEventListener("click", e => {
  const btn = e.target.closest(".more[data-menu]");
  if (!btn) { menu.classList.add("hidden"); return; }
  e.stopPropagation();
  const kind = btn.dataset.menu, i = +btn.dataset.i;
  if (menuCtx && menuCtx.btn === btn && !menu.classList.contains("hidden")) { menu.classList.add("hidden"); return; }
  menuCtx = { kind, i, btn };
  menu.innerHTML = MENUS[kind](db[kind][i]).map(([label, act, danger]) => `<button role="menuitem" data-act="${act}" class="${danger ? "danger" : ""}">${label}</button>`).join("");
  const r = btn.getBoundingClientRect();
  menu.classList.remove("hidden");
  menu.style.top = Math.min(window.scrollY + r.bottom + 4, window.scrollY + window.innerHeight - menu.offsetHeight - 8) + "px";
  menu.style.left = Math.max(8, window.scrollX + r.right - menu.offsetWidth) + "px";
});
menu.addEventListener("click", e => {
  const b = e.target.closest("[data-act]"); if (!b) return;
  const { kind, i } = menuCtx, rec = db[kind][i], act = b.dataset.act;
  menu.classList.add("hidden");
  if (act === "edit") return openModal(SINGULAR[kind], i);
  if (act === "delete") {
    if (!confirm("Delete this " + SINGULAR[kind] + "? This cannot be undone.")) return;
    db[kind].splice(i, 1); log("orange", SINGULAR[kind][0].toUpperCase() + SINGULAR[kind].slice(1) + " deleted", rec.name || rec.id); toast("Deleted."); return render();
  }
  if (act === "toggle") { rec.status = rec.status === "Active" ? "Suspended" : "Active"; log("orange", "Account " + rec.status.toLowerCase(), rec.name); toast(rec.name + " is now " + rec.status.toLowerCase() + "."); }
  if (act.startsWith("status:")) { rec.status = act.slice(7); log("blue", "Exam status changed", rec.name + " → " + rec.status); toast("Status set to " + rec.status + "."); }
  if (act === "publish") { rec.status = rec.status === "Pending" ? "Published" : "Pending"; if (rec.status === "Published") rec.graded = rec.submitted; log("purple", rec.status === "Published" ? "Results published" : "Results withdrawn", rec.exam); toast("Results " + rec.status.toLowerCase() + "."); }
  render();
});
window.addEventListener("scroll", () => menu.classList.add("hidden"), { passive: true });
document.addEventListener("keydown", e => { if (e.key === "Escape") { menu.classList.add("hidden"); if (!modal.classList.contains("hidden")) closeModal(); } });

/* ---------- exports & reports ---------- */
$("exportResults").onclick = () => { download("exam-results.csv", [["Examination", "Course", "Submitted", "Graded", "Status"], ...db.results.map(r => [r.exam, r.course, r.submitted, r.graded, r.status])]); toast("Results exported."); };
const REPORTS = {
  exam: ["examination-report.csv", () => [["Examination", "Course", "Date", "Duration", "Students", "Status"], ...db.exams.map(e => [e.name, e.course, e.date, e.duration, e.students, e.status])]],
  student: ["student-performance.csv", () => [["Examination", "Course", "Submitted", "Graded", "Graded %", "Status"], ...db.results.map(r => [r.exam, r.course, r.submitted, r.graded, r.submitted ? Math.round(r.graded / r.submitted * 100) + "%" : "0%", r.status])]],
  activity: ["system-activity.csv", () => [["Time", "Event", "Details"], ...db.activity.map(a => [new Date(a.ts).toLocaleString("en-GB"), a.title, a.text])]],
  course: ["course-report.csv", () => { const m = {}; db.exams.forEach(e => { const c = e.course.toUpperCase(); (m[c] = m[c] || { n: 0, s: 0 }); m[c].n++; m[c].s += Number(e.students) || 0; }); return [["Course", "Examinations", "Registered students"], ...Object.entries(m).map(([c, v]) => [c, v.n, v.s])]; }]
};
document.querySelectorAll(".report-card").forEach(b => b.onclick = () => { const [f, rows] = REPORTS[b.dataset.report]; download(f, rows()); toast("Report downloaded."); });

/* ---------- settings, notifications, sign-out ---------- */
function loadSettings() { const s = db.settings; $("setUni").value = s.uni; $("setSys").value = s.sys; $("setMail").value = s.mail; $("setDuration").value = s.duration; $("setAuto").checked = s.auto; $("setApprove").checked = s.approve; }
document.querySelectorAll(".save").forEach(b => b.onclick = () => {
  if (!$("setMail").checkValidity()) return toast("Please enter a valid support email.");
  db.settings = { uni: $("setUni").value.trim(), sys: $("setSys").value.trim(), mail: $("setMail").value.trim(), duration: $("setDuration").value, auto: $("setAuto").checked, approve: $("setApprove").checked };
  save(); toast("Settings saved successfully.");
});
$("notificationBtn").onclick = () => { const p = db.results.filter(r => r.status === "Pending").length; toast(p ? p + " result set(s) awaiting approval." : "No pending notifications."); };
$("logoutBtn").onclick = () => { if (confirm("Sign out of the administrator dashboard?")) SUSLSession.signOut(); };

/* ---------- init ---------- */
const hr = new Date().getHours();
const name = (session && session.user && session.user.name) || "Administrator";
$("greeting").textContent = (hr < 12 ? "Good morning" : hr < 17 ? "Good afternoon" : "Good evening") + ", " + name;
$("profileName").textContent = name; $("avatar").textContent = name[0].toUpperCase();
loadSettings(); render();
