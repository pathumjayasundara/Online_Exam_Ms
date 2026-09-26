"use strict";
/* ExamPortal — Administrator interface.
   Backed by backend/core-api (Flask). All data shown here is real,
   persisted server-side; every add/edit/delete/publish action is an API
   call. See assets/config.js to change the API's host/port. */

const session = SUSLSession.require("admin");
const $ = id => document.getElementById(id);
const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const API = ((window.EXAMPORTAL_CONFIG || {}).CORE_API || "http://127.0.0.1:5000") + "/api/admin";

/* ---------- API helper ---------- */
async function api(path, options = {}) {
  const token = localStorage.getItem("examportal_admin_token");
  let res;
  try {
    res = await fetch(API + path, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: "Bearer " + token } : {}),
        ...(options.headers || {})
      }
    });
  } catch (e) {
    toast("Cannot reach the backend at " + API + ". Is it running?");
    throw e;
  }
  if (res.status === 401) { SUSLSession.signOut(); return; }
  let data = {};
  try { data = await res.json(); } catch (e) { /* no body */ }
  if (!res.ok) throw new Error(data.error || data.message || ("Request failed (" + res.status + ")"));
  return data;
}

/* ---------- local cache, populated from the API ---------- */
let db = { exams: [], students: [], lecturers: [], questions: [], results: [], activity: [],
           settings: { uni: "", sys: "", mail: "", duration: "60 minutes", auto: true, approve: true } };

async function loadAll() {
  const [exams, students, lecturers, questions, results, activity, settings] = await Promise.all([
    api("/exams"), api("/students"), api("/lecturers"), api("/questions"),
    api("/results"), api("/activity"), api("/settings")
  ]);
  db.exams = exams || []; db.students = students || []; db.lecturers = lecturers || [];
  db.questions = questions || []; db.results = results || []; db.activity = activity || [];
  db.settings = settings || db.settings;
}

async function refreshActivity() { db.activity = await api("/activity") || []; }

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
  $("examCount").textContent = db.exams.length;
  $("studentCount").textContent = db.students.length.toLocaleString();
  $("completedCount").textContent = db.exams.filter(e => e.status === "Completed").length;
  $("pendingCount").textContent = String(db.results.filter(r => r.status === "Pending").length).padStart(2, "0");
  $("qTotal").textContent = db.questions.length.toLocaleString();
  $("qMcq").textContent = n(x => x.type === "Multiple Choice").toLocaleString();
  $("qWritten").textContent = n(x => x.type !== "Multiple Choice").toLocaleString();

  $("activityList").innerHTML = db.activity.map(a => `<div class="activity"><b class="dot ${esc(a.c)}-dot"></b><div><strong>${esc(a.title)}</strong><p>${esc(a.text)}</p><small>${ago(a.ts)}</small></div></div>`).join("") || `<p class="empty">No recent activity.</p>`;
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
    { k: "year", label: "Academic Year", type: "select", opts: ["1", "2", "3", "4"] } ] },
  lecturer: { list: "lecturers", title: "Lecturer", fields: [
    { k: "name", label: "Full Name", req: 1 },
    { k: "email", label: "Email", type: "email", req: 1 },
    { k: "dept", label: "Department", type: "select", opts: ["Computing", "Information Systems", "Physical Sciences & Technology"] },
    { k: "courses", label: "Assigned Courses", type: "number", min: 0, def: 1 } ] },
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

/* Each entity type -> { create(rec), update(id, rec) } talking to the real API. */
const API_OPS = {
  exam: {
    create: rec => api("/exams", { method: "POST", body: JSON.stringify(rec) }),
    update: (id, rec) => api(`/exams/${id}`, { method: "PUT", body: JSON.stringify(rec) })
  },
  student: {
    create: rec => api("/students", { method: "POST", body: JSON.stringify(rec) }),
    update: (id, rec) => api(`/students/${id}`, { method: "PUT", body: JSON.stringify(rec) })
  },
  lecturer: {
    create: rec => api("/lecturers", { method: "POST", body: JSON.stringify(rec) }),
    update: (id, rec) => api(`/lecturers/${id}`, { method: "PUT", body: JSON.stringify(rec) })
  },
  question: {
    create: rec => api("/questions", { method: "POST", body: JSON.stringify(rec) }),
    update: (id, rec) => api(`/questions/${id}`, { method: "PUT", body: JSON.stringify(rec) })
  }
};

$("modalForm").addEventListener("submit", async e => {
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
  if (type === "exam") rec.students = Number(rec.students) || 0;
  if (type === "question") rec.marks = Number(rec.marks);

  const submitBtn = $("modalForm").querySelector("[type=submit]");
  if (submitBtn) submitBtn.disabled = true;
  try {
    const list = db[f.list];
    if (index != null) {
      const current = list[index];
      const updated = await API_OPS[type].update(current.id, rec);
      Object.assign(list[index], updated);
      toast(f.title + " updated.");
    } else {
      const created = await API_OPS[type].create(rec);
      list.unshift(created);
      toast(f.title + " added successfully.");
    }
    await refreshActivity();
    closeModal(); render();
  } catch (err) {
    const dupField = type === "student" ? "reg" : type === "lecturer" ? "email" : null;
    if (dupField) $("e_" + dupField).textContent = err.message;
    else toast(err.message || "Something went wrong.");
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
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
const DELETE_PATH = { exams: id => `/exams/${id}`, students: id => `/students/${id}`, lecturers: id => `/lecturers/${id}`, questions: id => `/questions/${id}` };
const TOGGLE_PATH = { students: id => `/students/${id}/toggle-status`, lecturers: id => `/lecturers/${id}/toggle-status` };
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
menu.addEventListener("click", async e => {
  const b = e.target.closest("[data-act]"); if (!b) return;
  const { kind, i } = menuCtx, rec = db[kind][i], act = b.dataset.act;
  menu.classList.add("hidden");
  try {
    if (act === "edit") return openModal(SINGULAR[kind], i);

    if (act === "delete") {
      if (!confirm("Delete this " + SINGULAR[kind] + "? This cannot be undone.")) return;
      await api(DELETE_PATH[kind](rec.id), { method: "DELETE" });
      db[kind].splice(i, 1);
      toast("Deleted.");
    } else if (act === "toggle") {
      const updated = await api(TOGGLE_PATH[kind](rec.id), { method: "POST" });
      Object.assign(rec, updated);
      toast(rec.name + " is now " + rec.status.toLowerCase() + ".");
    } else if (act.startsWith("status:")) {
      const newStatus = act.slice(7);
      const updated = await api(`/exams/${rec.id}`, { method: "PUT", body: JSON.stringify({ status: newStatus }) });
      Object.assign(rec, updated);
      toast("Status set to " + newStatus + ".");
    } else if (act === "publish") {
      const updated = await api(`/results/${rec.id}/publish`, { method: "POST" });
      Object.assign(rec, updated);
      toast("Results " + rec.status.toLowerCase() + ".");
    }
    await refreshActivity();
    render();
  } catch (err) {
    toast(err.message || "Something went wrong.");
  }
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
document.querySelectorAll(".save").forEach(b => b.onclick = async () => {
  if (!$("setMail").checkValidity()) return toast("Please enter a valid support email.");
  const payload = { uni: $("setUni").value.trim(), sys: $("setSys").value.trim(), mail: $("setMail").value.trim(), duration: $("setDuration").value, auto: $("setAuto").checked, approve: $("setApprove").checked };
  try {
    db.settings = await api("/settings", { method: "PUT", body: JSON.stringify(payload) });
    toast("Settings saved successfully.");
  } catch (err) { toast(err.message || "Could not save settings."); }
});
$("notificationBtn").onclick = () => { const p = db.results.filter(r => r.status === "Pending").length; toast(p ? p + " result set(s) awaiting approval." : "No pending notifications."); };
$("logoutBtn").onclick = () => { if (confirm("Sign out of the administrator dashboard?")) SUSLSession.signOut(); };

/* ---------- init ---------- */
(async function init() {
  const hr = new Date().getHours();
  const name = (session && session.user && session.user.name) || "Administrator";
  $("greeting").textContent = (hr < 12 ? "Good morning" : hr < 17 ? "Good afternoon" : "Good evening") + ", " + name;
  $("profileName").textContent = name; $("avatar").textContent = name[0].toUpperCase();

  try {
    await loadAll();
  } catch (err) {
    toast(err.message || "Could not load data from the backend.");
  }
  loadSettings();
  render();
})();
