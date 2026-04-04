const navToggle = document.querySelector(".nav-toggle");
const navLinks = document.querySelector(".nav-links");

if (navToggle && navLinks) {
  navToggle.addEventListener("click", () => {
    const isOpen = navLinks.classList.toggle("is-open");
    navToggle.setAttribute("aria-expanded", String(isOpen));
  });
}

const forms = [
  {
    form: document.getElementById("hero-signup"),
    message: document.getElementById("hero-message")
  },
  {
    form: document.getElementById("footer-signup"),
    message: document.getElementById("footer-message")
  }
];

forms.forEach(({ form, message }) => {
  if (!form || !message) {
    return;
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();

    const emailInput = form.querySelector('input[type="email"]');

    if (!emailInput || !emailInput.value.trim()) {
      message.textContent = "Enter an email address to request early access.";
      return;
    }

    if (!emailInput.checkValidity()) {
      message.textContent = "Use a valid email address before submitting.";
      return;
    }

    message.textContent = "Thanks. Your interest has been captured for the local alpha list.";
    form.reset();
  });
});
