// ========== CREDENTIALS ==========
const credentials = {
  admin: {
    email: 'admin@sab.ac.lk',
    password: 'Admin@SUSL2026'
  },
  lecturer: {
    email: 'lecturer@sab.ac.lk',
    password: 'SUSLLECT2026'
  },
  student: {
    email: 'student@sab.ac.lk',
    password: 'PST1234'
  }
};

let currentRole = 'admin';
let pwdVisible  = false;

// ========== ROLE SELECTION ==========
function selectRole(role) {
  currentRole = role;

  // Update active card
  ['admin', 'lecturer', 'student'].forEach(r => {
    const card = document.getElementById('card-' + r);
    card.classList.toggle('active', r === role);
  });

  // Auto-fill credentials
  document.getElementById('email').value    = credentials[role].email;
  document.getElementById('password').value = credentials[role].password;

  // Reset password visibility
  if (pwdVisible) togglePassword();
}

// ========== PASSWORD TOGGLE ==========
function togglePassword() {
  pwdVisible = !pwdVisible;
  const input    = document.getElementById('password');
  const eyeOpen  = document.getElementById('eye-open');
  const eyeClosed = document.getElementById('eye-closed');

  input.type = pwdVisible ? 'text' : 'password';
  eyeOpen.style.display  = pwdVisible ? 'none'  : 'block';
  eyeClosed.style.display = pwdVisible ? 'block' : 'none';
}

// ========== SIGN IN HANDLER ==========
function handleSignIn() {
  const email    = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;

  if (!email) {
    showToast('Please enter your email address.', 'error');
    return;
  }

  if (!password) {
    showToast('Please enter your password.', 'error');
    return;
  }

  // Check credentials
  const cred = credentials[currentRole];

  if (email === cred.email && password === cred.password) {
    const roleLabel = currentRole.charAt(0).toUpperCase() + currentRole.slice(1);
    showToast('Signing in as ' + roleLabel + '…', 'success');

    // Simulate redirect after a short delay
    setTimeout(() => {
      showToast('Redirecting to your dashboard…', 'info');
    }, 1800);

  } else {
    showToast('Invalid email or password. Please try again.', 'error');
  }
}

// ========== TOAST NOTIFICATION ==========
let toastTimer = null;

function showToast(message, type = 'info') {
  const toast = document.getElementById('toast');

  // Clear previous timer
  if (toastTimer) clearTimeout(toastTimer);

  // Reset classes
  toast.className = 'toast';
  toast.textContent = message;

  // Force reflow so animation triggers properly
  void toast.offsetWidth;

  toast.classList.add(type, 'show');

  toastTimer = setTimeout(() => {
    toast.classList.remove('show');
  }, 3200);
}

// ========== KEYBOARD SUPPORT ==========
document.addEventListener('DOMContentLoaded', () => {
  // Allow pressing Enter in password field to sign in
  document.getElementById('password').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleSignIn();
  });

  document.getElementById('email').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') document.getElementById('password').focus();
  });

  // Keyboard navigation for role cards (accessibility)
  ['admin', 'lecturer', 'student'].forEach((role, index) => {
    const card = document.getElementById('card-' + role);
    card.setAttribute('tabindex', '0');
    card.setAttribute('role', 'button');
    card.setAttribute('aria-label', role.charAt(0).toUpperCase() + role.slice(1) + ' role');

    card.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        selectRole(role);
      }
    });
  });

  // Set initial state
  selectRole('admin');

  // ========== BUTTON CLICK SCALE: 1 → 0.98 → 1 ==========
  const btn = document.querySelector('.btn-signin');
  btn.addEventListener('click', () => {
    btn.style.transition = 'transform 0.08s ease';
    btn.style.transform  = 'scale(0.98)';
    setTimeout(() => {
      btn.style.transform  = 'scale(1)';
      setTimeout(() => {
        btn.style.transform  = '';
        btn.style.transition = '';
      }, 120);
    }, 90);
  });
});
