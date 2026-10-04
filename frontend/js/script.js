function getFormData() {
  const form = document.getElementById('trip-form');
  const fd = new FormData(form);

  const interests = Array.from(
    document.querySelectorAll('input[name="interests"]:checked')
  ).map((el) => el.value);

  const data = {
    destination: fd.get('destination'),
    departureCity: (fd.get('departureCity') || '').trim(),
    startDate: fd.get('startDate') || '',
    endDate: fd.get('endDate') || '',
    budgetUSD: Number.parseFloat(fd.get('budgetUSD') || '0') || 0,
    age: fd.get('age') || '',
    gender: fd.get('gender') || '',
    travelers: fd.get('travelers') || 1,
    interests,
  };
  return data;
}

function validateDates() {
  const start = document.getElementById('startDate').value;
  const end = document.getElementById('endDate').value;
  if (start && end && new Date(end) < new Date(start)) {
    alert('End date must be the same as or after the start date.');
    return false;
  }
  return true;
}

document.getElementById('trip-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!validateDates()) return;

  const data = getFormData();
  if (data.budgetUSD <= 0) {
    alert('Please enter a valid budget in USD.');
    return;
  }

  const btn = e.submitter || document.querySelector('#trip-form button[type="submit"]');
  const label = btn ? btn.innerHTML : '';
  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Planning your trip...';
  }

  try {
    const resp = await fetch('/api/plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${await resp.text()}`);

    sessionStorage.setItem('plan', JSON.stringify(await resp.json()));
    sessionStorage.setItem('destinai_form_data', JSON.stringify(data));
    window.location.href = 'output.html';
  } catch (err) {
    console.error(err);
    alert('Something went wrong. Please try again.');
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = label;
    }
  }
});
