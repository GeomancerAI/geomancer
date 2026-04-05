const navToggle = document.querySelector('.nav-toggle');
const navLinks = document.querySelector('.nav-links');

if (navToggle && navLinks) {
  navToggle.addEventListener('click', () => {
    const isOpen = navLinks.classList.toggle('is-open');
    navToggle.setAttribute('aria-expanded', String(isOpen));
  });
}

const FORM_ENDPOINT = 'https://formspree.io/f/xreooykq';
const bodyPage = document.body.dataset.page;
const formPageMap = {
  home: 'homepage',
  'early-access': 'early-access'
};
const formPage = formPageMap[bodyPage];

const modal = document.getElementById('early-access-modal');
const modalContent = document.getElementById('ea-modal-content');
const dialog = modal?.querySelector('.ea-modal-dialog');
const closeTriggers = modal ? modal.querySelectorAll('[data-modal-close]') : [];
const forms = Array.from(document.querySelectorAll('.signup-form'));

const focusableSelector = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])'
].join(',');

let activeFormState = null;
let lastFocusedElement = null;
let isSubmitting = false;

function setFormMessage(messageElement, text, type = 'default') {
  if (!messageElement) {
    return;
  }

  messageElement.textContent = text;
  messageElement.dataset.state = type;
}

function validateEmailInput(emailInput, messageElement) {
  if (!emailInput || !emailInput.value.trim()) {
    emailInput?.setAttribute('aria-invalid', 'true');
    setFormMessage(messageElement, 'Enter an email address to request early access.', 'error');
    return false;
  }

  if (!emailInput.checkValidity()) {
    emailInput.setAttribute('aria-invalid', 'true');
    setFormMessage(messageElement, 'Use a valid email address before submitting.', 'error');
    return false;
  }

  emailInput.removeAttribute('aria-invalid');
  setFormMessage(messageElement, '', 'default');
  return true;
}

function escapeHtml(value) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function getFocusableElements() {
  if (!modal || modal.hidden || !dialog) {
    return [];
  }

  return Array.from(dialog.querySelectorAll(focusableSelector)).filter((element) => {
    return !element.hasAttribute('hidden') && element.getAttribute('aria-hidden') !== 'true';
  });
}

function focusFirstElement() {
  const focusableElements = getFocusableElements();
  const firstElement = focusableElements[0] || dialog;
  requestAnimationFrame(() => {
    firstElement?.focus();
  });
}

function closeModal() {
  if (!modal || isSubmitting) {
    return;
  }

  modal.hidden = true;
  document.body.classList.remove('modal-open');
  document.removeEventListener('keydown', handleModalKeydown);
  modalContent.innerHTML = '';
  activeFormState = null;

  if (lastFocusedElement) {
    lastFocusedElement.focus();
  }
}

function handleModalKeydown(event) {
  if (!modal || modal.hidden) {
    return;
  }

  if (event.key === 'Escape') {
    event.preventDefault();
    closeModal();
    return;
  }

  if (event.key !== 'Tab') {
    return;
  }

  const focusableElements = getFocusableElements();

  if (!focusableElements.length) {
    event.preventDefault();
    dialog?.focus();
    return;
  }

  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  if (event.shiftKey && document.activeElement === firstElement) {
    event.preventDefault();
    lastElement.focus();
  } else if (!event.shiftKey && document.activeElement === lastElement) {
    event.preventDefault();
    firstElement.focus();
  }
}

function renderConfirmState(errorMessage = '') {
  if (!modalContent || !activeFormState) {
    return;
  }

  const safeEmail = escapeHtml(activeFormState.email);

  modalContent.innerHTML = `
    <div class="ea-modal-header">
      <p class="ea-modal-eyebrow">Early Access</p>
      <h2 class="ea-modal-title" id="ea-modal-title">Confirm your early access request</h2>
      <p class="ea-modal-description" id="ea-modal-description">You’re requesting Geomancer early access and launch updates by email.</p>
    </div>
    <div class="ea-modal-email-row">
      <span class="ea-modal-email-label">Email</span>
      <strong class="ea-modal-email-value">${safeEmail}</strong>
    </div>
    <label class="ea-modal-checkbox-row" for="ea-consent">
      <input class="ea-modal-checkbox" id="ea-consent" type="checkbox">
      <span>I agree to receive Geomancer early access and launch updates by email.</span>
    </label>
    <p class="ea-modal-legal">
      Review our <a href="privacy.html">Privacy Policy</a> and <a href="terms.html">Terms of Use</a>.
    </p>
    <p class="ea-modal-feedback${errorMessage ? ' is-error' : ''}" id="ea-modal-feedback" role="status" aria-live="polite">${errorMessage}</p>
    <div class="ea-modal-actions">
      <button class="button-primary" id="ea-confirm-button" type="button" disabled>Confirm Request</button>
      <button class="ea-modal-secondary" id="ea-cancel-button" type="button" data-modal-close>Cancel</button>
    </div>
  `;

  const consentCheckbox = modalContent.querySelector('#ea-consent');
  const confirmButton = modalContent.querySelector('#ea-confirm-button');
  const cancelButton = modalContent.querySelector('#ea-cancel-button');

  consentCheckbox?.addEventListener('change', () => {
    confirmButton.disabled = !consentCheckbox.checked;
  });

  confirmButton?.addEventListener('click', submitEarlyAccessRequest);
  cancelButton?.addEventListener('click', closeModal);
  focusFirstElement();
}

function renderLoadingState() {
  if (!modalContent || !activeFormState) {
    return;
  }

  const safeEmail = escapeHtml(activeFormState.email);

  modalContent.innerHTML = `
    <div class="ea-modal-header">
      <p class="ea-modal-eyebrow">Early Access</p>
      <h2 class="ea-modal-title" id="ea-modal-title">Confirm your early access request</h2>
      <p class="ea-modal-description" id="ea-modal-description">You’re requesting Geomancer early access and launch updates by email.</p>
    </div>
    <div class="ea-modal-email-row">
      <span class="ea-modal-email-label">Email</span>
      <strong class="ea-modal-email-value">${safeEmail}</strong>
    </div>
    <div class="ea-modal-loading" role="status" aria-live="polite">
      <span class="ea-modal-loading-dot" aria-hidden="true"></span>
      <span>Requesting...</span>
    </div>
    <div class="ea-modal-actions">
      <button class="button-primary" type="button" disabled>Requesting...</button>
      <button class="ea-modal-secondary" type="button" disabled>Cancel</button>
    </div>
  `;

  dialog?.focus();
}

function renderSuccessState() {
  if (!modalContent) {
    return;
  }

  modalContent.innerHTML = `
    <div class="ea-modal-success-mark" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path d="M5 12.5 9.2 16.5 19 7.5"></path>
      </svg>
    </div>
    <div class="ea-modal-header ea-modal-header-success">
      <p class="ea-modal-eyebrow">Early Access</p>
      <h2 class="ea-modal-title" id="ea-modal-title">You’re on the list</h2>
      <p class="ea-modal-description" id="ea-modal-description">Thanks for requesting early access to Geomancer. We’ll email you when the Windows alpha is ready, along with major updates as we get closer to launch.</p>
    </div>
    <p class="ea-modal-subtext">No spam. Just launch updates and early access news.</p>
    <div class="ea-modal-actions ea-modal-actions-single">
      <button class="button-primary" id="ea-close-success" type="button">Close</button>
    </div>
  `;

  const closeButton = modalContent.querySelector('#ea-close-success');
  closeButton?.addEventListener('click', closeModal);
  focusFirstElement();
}

async function submitEarlyAccessRequest() {
  if (!activeFormState || isSubmitting) {
    return;
  }

  isSubmitting = true;
  renderLoadingState();

  try {
    const response = await fetch(FORM_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json'
      },
      body: JSON.stringify({
        email: activeFormState.email,
        _subject: 'New Geomancer Early Access Request',
        _source: 'geomancer-site',
        page: activeFormState.page
      })
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok || data.errors) {
      throw new Error('Formspree submission failed');
    }

    setFormMessage(activeFormState.messageElement, '', 'default');
    activeFormState.form.reset();
    activeFormState.form.querySelector('input[type="email"]')?.removeAttribute('aria-invalid');
    renderSuccessState();
  } catch (error) {
    renderConfirmState('Something went wrong while submitting your request. Please try again.');
  } finally {
    isSubmitting = false;
  }
}

function openModal(formState) {
  if (!modal || !dialog) {
    return;
  }

  activeFormState = formState;
  lastFocusedElement = formState.triggerButton;
  isSubmitting = false;
  renderConfirmState();
  modal.hidden = false;
  document.body.classList.add('modal-open');
  document.addEventListener('keydown', handleModalKeydown);
}

if (modal) {
  closeTriggers.forEach((trigger) => {
    trigger.addEventListener('click', (event) => {
      if (isSubmitting) {
        event.preventDefault();
        return;
      }

      closeModal();
    });
  });
}

if (formPage && modal) {
  forms.forEach((form) => {
    const messageElement = form.nextElementSibling?.nextElementSibling?.classList.contains('form-message')
      ? form.nextElementSibling.nextElementSibling
      : form.parentElement?.querySelector('.form-message');
    const emailInput = form.querySelector('input[type="email"]');
    const triggerButton = form.querySelector('button[type="submit"]');

    if (!emailInput || !triggerButton || !messageElement) {
      return;
    }

    emailInput.addEventListener('input', () => {
      if (emailInput.validity.valid) {
        emailInput.removeAttribute('aria-invalid');
        setFormMessage(messageElement, '', 'default');
      }
    });

    form.addEventListener('submit', (event) => {
      event.preventDefault();

      if (!validateEmailInput(emailInput, messageElement)) {
        emailInput.focus();
        return;
      }

      openModal({
        form,
        email: emailInput.value.trim(),
        messageElement,
        triggerButton,
        page: formPage
      });
    });
  });
}
