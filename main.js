// main.js - Client-side scripts for Edgars Performance Tracker

document.addEventListener("DOMContentLoaded", function () {
    // 1. Auto-populate 'Test Date' field with today's date if empty
    const dateInput = document.querySelector('input[name="session_date"]');
    if (dateInput && !dateInput.value) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.value = today;
    }

    // 2. Client-side input validation for pitch-side metric bounds
    const metricForm = document.querySelector('form[action*="record_metric"]');
    if (metricForm) {
        metricForm.addEventListener('submit', function (e) {
            const sprint = parseFloat(document.querySelector('input[name="sprint_30m_sec"]').value);
            const agility = parseFloat(document.querySelector('input[name="agility_test_sec"]').value);
            const passing = parseFloat(document.querySelector('input[name="passing_accuracy_pct"]').value);
            const stamina = parseFloat(document.querySelector('input[name="stamina_score"]').value);
            const rating = parseFloat(document.querySelector('input[name="coach_rating"]').value);

            if (sprint <= 0 || agility <= 0) {
                alert("Sprint and agility times must be greater than 0 seconds.");
                e.preventDefault();
                return false;
            }

            if (passing < 0 || passing > 100 || stamina < 0 || stamina > 100) {
                alert("Passing accuracy and Stamina index must be between 0 and 100.");
                e.preventDefault();
                return false;
            }

            if (rating < 1 || rating > 10) {
                alert("Coach rating must be between 1.0 and 10.0.");
                e.preventDefault();
                return false;
            }
        });
    }
});