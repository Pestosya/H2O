// admin/static/script.js

document.addEventListener("DOMContentLoaded", () => {
  // Эффект «рябь» на кнопках при клике
  document.querySelectorAll(".ripple").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const rect = btn.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const rippleEl = document.createElement("span");
      rippleEl.style.left = `${x}px`;
      rippleEl.style.top = `${y}px`;
      rippleEl.classList.add("ripple-effect");
      btn.appendChild(rippleEl);

      setTimeout(() => {
        rippleEl.remove();
      }, 600);
    });
  });
});
