requireAuth();

// TODO: swap for the team's real inbox before shipping.
const SUPPORT_EMAIL = "support@dermalyze.app";

const searchInput = document.getElementById("faq-search");
const items = Array.from(document.querySelectorAll(".faq-item"));
const emptyEl = document.getElementById("faq-empty");

searchInput.addEventListener("input", () => {
  const q = searchInput.value.trim().toLowerCase();
  let anyVisible = false;
  items.forEach((item) => {
    const match = !q || item.dataset.q.includes(q) || item.textContent.toLowerCase().includes(q);
    item.classList.toggle("hidden", !match);
    if (match) anyVisible = true;
  });
  emptyEl.classList.toggle("hidden", anyVisible);
});

document.getElementById("contact-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const name = document.getElementById("contact-name").value.trim();
  const email = document.getElementById("contact-email").value.trim();
  const message = document.getElementById("contact-message").value.trim();

  const subject = encodeURIComponent(`Dermalyze support request from ${name}`);
  const body = encodeURIComponent(`${message}\n\n— ${name} (${email})`);
  window.location.href = `mailto:${SUPPORT_EMAIL}?subject=${subject}&body=${body}`;
});
