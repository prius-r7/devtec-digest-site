// Set current year in footer
document.addEventListener('DOMContentLoaded', () => {
  const yearEl = document.getElementById('year');
  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }

  // Pricing toggle
  const billingToggle = document.getElementById('billing-toggle');
  const amounts = document.querySelectorAll('.amount');
  const periodEls = document.querySelectorAll('.period');

  function updatePrices() {
    const yearly = billingToggle.checked;
    amounts.forEach((el) => {
      const monthlyPrice = el.getAttribute('data-monthly');
      const yearlyPrice = el.getAttribute('data-yearly');
      el.textContent = yearly ? yearlyPrice : monthlyPrice;
    });
    periodEls.forEach((el) => {
      el.textContent = yearly ? ' /yr' : ' /mo';
    });
  }

  if (billingToggle) {
    billingToggle.addEventListener('change', updatePrices);
  }
  updatePrices();
});
