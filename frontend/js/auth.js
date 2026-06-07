/* ─────────────────────────────────────────
   auth.js  —  Login / Signup logic
───────────────────────────────────────── */

const loginForm  = document.getElementById("login-form");
const signupForm = document.getElementById("signup-form");
const authError  = document.getElementById("auth-error");
const tabLogin   = document.getElementById("tab-login");
const tabSignup  = document.getElementById("tab-signup");

function showAuthError(msg) {
  authError.textContent = msg;
  authError.style.display = "block";
  setTimeout(() => authError.style.display = "none", 4000);
}

function switchTab(tab) {
  if (tab === "login") {
    loginForm.style.display  = "block";
    signupForm.style.display = "none";
    tabLogin.classList.add("active");
    tabSignup.classList.remove("active");
  } else {
    loginForm.style.display  = "none";
    signupForm.style.display = "block";
    tabSignup.classList.add("active");
    tabLogin.classList.remove("active");
  }
  authError.style.display = "none";
}

tabLogin.addEventListener("click",  () => switchTab("login"));
tabSignup.addEventListener("click", () => switchTab("signup"));

/* ── Login ─────────────────────────────────────────────── */
loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = loginForm.querySelector("button[type=submit]");
  const username = document.getElementById("login-username").value.trim();
  const password = document.getElementById("login-password").value;
  if (!username || !password) return showAuthError("Please fill in all fields.");
  btn.disabled = true;
  btn.textContent = "Signing in…";
  try {
    const data = await apiPost("/auth/login", { username, password }, false);
    setSession(data);
    checkAuth();
    checkModelStatus();
    toast(`Welcome back, ${data.username}! 👋`, "success");
  } catch (err) {
    showAuthError(err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Sign In";
  }
});

/* ── Signup ────────────────────────────────────────────── */
signupForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = signupForm.querySelector("button[type=submit]");
  const username = document.getElementById("signup-username").value.trim();
  const password = document.getElementById("signup-password").value;
  const confirm  = document.getElementById("signup-confirm").value;
  if (!username || !password) return showAuthError("Please fill in all fields.");
  if (password !== confirm)   return showAuthError("Passwords do not match.");
  if (password.length < 6)   return showAuthError("Password must be ≥ 6 characters.");
  btn.disabled = true;
  btn.textContent = "Creating account…";
  try {
    await apiPost("/auth/signup", { username, password }, false);
    toast("Account created! Please log in.", "success");
    switchTab("login");
    document.getElementById("login-username").value = username;
  } catch (err) {
    showAuthError(err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Create Account";
  }
});
