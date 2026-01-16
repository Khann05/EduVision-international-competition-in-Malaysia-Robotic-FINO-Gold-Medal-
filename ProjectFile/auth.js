// ===============================
// auth.js – Eduvision FINAL
// ===============================

const STORAGE_KEY = "eduvisionUser";

// -------------------------------
// Helper: ambil user dari localStorage
// -------------------------------
function getCurrentUser() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    console.error("Failed to parse user from localStorage:", e);
    return null;
  }
}

// -------------------------------
// Update tampilan navbar
// -------------------------------
function updateNavAuth() {
  const navAuth   = document.querySelector(".nav-auth-buttons");
  const navUser   = document.querySelector(".nav-user-info");
  const nameSpan  = document.querySelector(".nav-user-name");
  const emailSpan = document.querySelector(".nav-user-email");

  const user = getCurrentUser();

  if (!navAuth || !navUser) return; // jaga-jaga kalau di halaman tertentu elemen tidak ada

  if (user) {
    // Sudah login
    navAuth.style.display = "none";
    navUser.style.display = "flex";

    if (nameSpan)  nameSpan.textContent  = user.fullname || user.name || "";
    if (emailSpan) emailSpan.textContent = user.email || "";
  } else {
    // Belum login
    navAuth.style.display = "flex";
    navUser.style.display = "none";

    if (nameSpan)  nameSpan.textContent  = "";
    if (emailSpan) emailSpan.textContent = "";
  }
}

// -------------------------------
// LOGIN (dipanggil dari form login)
// <form onsubmit="handleLogin(event)">
// -------------------------------
function handleLogin(event) {
  event.preventDefault();

  const form = event.target;
  const email    = form.email.value.trim();
  const password = form.password.value.trim();
  const msgEl    = form.querySelector(".form-message");

  if (!email || !password) {
    if (msgEl) {
      msgEl.textContent = "Please fill in email and password.";
      msgEl.style.color = "red";
    }
    return;
  }

  // NOTE: Ini masih dummy — nanti bisa diganti cek ke backend / Sheety
  const user = {
    email: email,
    fullname: email.split("@")[0] // contoh: ambil nama dari email
  };

  localStorage.setItem(STORAGE_KEY, JSON.stringify(user));

  if (msgEl) {
    msgEl.textContent = "Login success. Redirecting...";
    msgEl.style.color = "green";
  }

  updateNavAuth();

  // Redirect ke home
  window.location.replace("index.html#home");
}

// -------------------------------
// SIGN UP (dipanggil dari form signup)
// <form onsubmit="handleSignup(event)">
// -------------------------------
function handleSignup(event) {
  event.preventDefault();

  const form     = event.target;
  const fullname = form.fullname.value.trim();
  const email    = form.email.value.trim();
  const password = form.password.value.trim();
  const msgEl    = form.querySelector(".form-message");

  if (!fullname || !email || !password) {
    if (msgEl) {
      msgEl.textContent = "Please fill all fields.";
      msgEl.style.color = "red";
    }
    return;
  }

  const user = { fullname, email };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(user));

  if (msgEl) {
    msgEl.textContent = "Account created. Redirecting...";
    msgEl.style.color = "green";
  }

  updateNavAuth();
  window.location.replace("index.html#home");
}

// -------------------------------
// Show / hide password
// -------------------------------
function togglePassword(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;

  if (input.type === "password") {
    input.type = "text";
    if (btn) btn.textContent = "Hide";
  } else {
    input.type = "password";
    if (btn) btn.textContent = "Show";
  }
}

// -------------------------------
// LOGOUT (dipanggil dari tombol navbar)
// <button type="button" onclick="handleLogout()">Logout</button>
// -------------------------------
function handleLogout() {
  try {
    // Hapus data user
    localStorage.removeItem(STORAGE_KEY);
  } catch (e) {
    console.error("Error clearing storage:", e);
  }

  // Update tampilan (kalau masih di halaman yang sama sesaat sebelum redirect)
  updateNavAuth();

  // Redirect + refresh ke home
  // pakai replace supaya tombol Back tidak kembali ke state sudah-login
  window.location.replace("index.html#home");

  // Kalau mau cuma reload halaman yang sekarang:
  // window.location.reload();
}

// -------------------------------
// Saat halaman pertama kali dibuka
// -------------------------------
document.addEventListener("DOMContentLoaded", () => {
  updateNavAuth();
});
