// ========== CONFIG ==========
const CORE_API     = (window.EXAMPORTAL_CONFIG || {}).CORE_API || 'http://127.0.0.1:5000';
const LECTURER_API = (window.EXAMPORTAL_CONFIG || {}).LECTURER_API || 'http://127.0.0.1:5001';

// Demo accounts pre-filled for convenience.
//  - admin:    verified by the Flask API (backend/core-api); seeded automatically on first run.
//  - lecturer: verified by the Flask API (backend/lecturer-api); seeded automatically on first run.
//  - student:  no credentials here — the Student Portal has its own sign-in / register flow.
const credentials = {
  admin:    { email: 'admin@sab.ac.lk',  password: 'Admin@SUSL2026' },
  lecturer: { email: 'davis@susl.ac.lk', password: 'password123' }
};

let currentRole = 'admin';
let pwdVisible  = false;
let busy        = false;

// Already signed in? Go straight to the right portal.
(function resumeSession() {
  const s = window.SUSLSession && SUSLSession.get();
  if (s && (s.role === 'admin' || s.role === 'lecturer')) {
    window.location.replace(SUSLSession.homeFor(s.role));
  }
})();

// ========== ROLE SELECTION ==========
function selectRole(role) {
  currentRole = role;

  ['admin', 'lecturer', 'student'].forEach(r => {
    const card = document.getElementById('card-' + r);
    card.classList.toggle('active', r === role);
    card.setAttribute('aria-pressed', r === role ? 'true' : 'false');
  });

  const isStudent = role === 'student';
  document.getElementById('credFields').hidden   = isStudent;
  document.getElementById('studentPanel').hidden = !isStudent;

  if (!isStudent) {
    document.getElementById('email').value    = credentials[role].email;
    document.getElementById('password').value = credentials[role].password;
    document.getElementById('email').placeholder = credentials[role].email;
  }

  if (pwdVisible) togglePassword();
}

// ========== PASSWORD TOGGLE ==========
function togglePassword() {
  pwdVisible = !pwdVisible;
  const input     = document.getElementById('password');
  const eyeOpen   = document.getElementById('eye-open');
  const eyeClosed = document.getElementById('eye-closed');

  input.type = pwdVisible ? 'text' : 'password';
  eyeOpen.style.display   = pwdVisible ? 'none'  : 'block';
  eyeClosed.style.display = pwdVisible ? 'block' : 'none';
}

// ========== SIGN IN ==========
async function handleSignIn() {
  if (busy) return;

  const email    = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;

  if (!email)    { showToast('Please enter your email address.', 'error'); return; }
  if (!password) { showToast('Please enter your password.', 'error'); return; }

  setBusy(true);
  try {
    if (currentRole === 'admin')    await signInAdmin(email, password);
    if (currentRole === 'lecturer') await signInLecturer(email, password);
  } catch (err) {
    showToast(err.message || 'Sign in failed. Please try again.', 'error');
    setBusy(false);
  }
}

async function signInAdmin(email, password) {
  let res;
  try {
    res = await fetch(CORE_API + '/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, password: password, role: 'admin' })
    });
  } catch (e) {
    throw new Error('Cannot reach the Core API at ' + CORE_API + '. Start the backend first (see README).');
  }

  let data = {};
  try { data = await res.json(); } catch (e) { /* non-JSON error page */ }

  if (!res.ok || !data.token) {
    throw new Error(data.error || 'Invalid email or password. Please try again.');
  }

  // The admin portal reads these two keys on load and skips its own login box.
  localStorage.setItem('examportal_admin_token', data.token);
  localStorage.setItem('examportal_admin_user', JSON.stringify(data.user || {}));
  SUSLSession.set('admin', data.user || { email: email });
  finishSignIn('admin');
}

async function signInLecturer(email, password) {
  let res;
  try {
    res = await fetch(LECTURER_API + '/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, password: password })
    });
  } catch (e) {
    throw new Error('Cannot reach the Lecturer service at ' + LECTURER_API + '. Start the backend first (see README).');
  }

  let data = {};
  try { data = await res.json(); } catch (e) { /* non-JSON error page */ }

  if (!res.ok || !data.token) {
    throw new Error(data.message || 'Invalid email or password. Please try again.');
  }
  if (data.user && String(data.user.role).toLowerCase() !== 'lecturer') {
    throw new Error('This account is not a lecturer account.');
  }

  // The lecturer portal reads these two keys on load and skips its own login box.
  localStorage.setItem('examportal_token', data.token);
  localStorage.setItem('examportal_user', JSON.stringify(data.user || {}));
  SUSLSession.set('lecturer', data.user || { email: email });
  finishSignIn('lecturer');
}

function finishSignIn(role) {
  const label = role.charAt(0).toUpperCase() + role.slice(1);
  showToast('Signing in as ' + label + '…', 'success');
  setTimeout(() => { window.location.href = SUSLSession.homeFor(role); }, 600);
}

function continueToStudent() {
  window.location.href = SUSLSession.homeFor('student');
}

function forgotPassword(e) {
  e.preventDefault();
  showToast('Please contact the system administrator to reset your password.', 'info');
}

function setBusy(state) {
  busy = state;
  const btn = document.getElementById('signInBtn');
  if (!btn) return;
  btn.disabled = state;
  btn.style.opacity = state ? '0.7' : '';
  btn.textContent = state ? 'Signing in…' : 'Sign in securely';
}

// ========== TOAST NOTIFICATION ==========
let toastTimer = null;

function showToast(message, type = 'info') {
  const toast = document.getElementById('toast');
  if (toastTimer) clearTimeout(toastTimer);

  toast.className = 'toast';
  toast.textContent = message;
  toast.setAttribute('role', 'status');
  void toast.offsetWidth; // restart the animation

  toast.classList.add(type, 'show');
  toastTimer = setTimeout(() => toast.classList.remove('show'), 4200);
}

// ========== KEYBOARD SUPPORT ==========
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('password').addEventListener('keydown', e => {
    if (e.key === 'Enter') handleSignIn();
  });
  document.getElementById('email').addEventListener('keydown', e => {
    if (e.key === 'Enter') document.getElementById('password').focus();
  });

  ['admin', 'lecturer', 'student'].forEach(role => {
    const card = document.getElementById('card-' + role);
    card.setAttribute('tabindex', '0');
    card.setAttribute('role', 'button');
    card.setAttribute('aria-label', role.charAt(0).toUpperCase() + role.slice(1) + ' role');
    card.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectRole(role); }
    });
  });

  selectRole('admin');

  // Button press feedback: 1 → 0.98 → 1
  document.querySelectorAll('.btn-signin').forEach(btn => {
    btn.addEventListener('click', () => {
      btn.style.transition = 'transform 0.08s ease';
      btn.style.transform  = 'scale(0.98)';
      setTimeout(() => {
        btn.style.transform = 'scale(1)';
        setTimeout(() => { btn.style.transform = ''; btn.style.transition = ''; }, 120);
      }, 90);
    });
  });
});
