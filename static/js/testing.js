/**
 * Testing section: timer and progress bar on take-test/result pages.
 * No inline scripts in templates — this file runs only when included.
 */
(function() {
    // Timer logic
    var timerEl = document.getElementById('timer');
    var form = document.getElementById('submit-test-form');
    if (timerEl && timerEl.dataset.endsAt) {
        var endsAt = new Date(timerEl.dataset.endsAt);

        function updateTimer() {
            var now = new Date();
            var left = Math.max(0, Math.floor((endsAt - now) / 1000));
            if (left <= 0) {
                timerEl.textContent = 'Время вышло';
                timerEl.classList.add('testing-timer--danger');
                if (form) form.submit();
                return;
            }
            var m = Math.floor(left / 60);
            var s = left % 60;
            timerEl.textContent = m + ':' + (s < 10 ? '0' : '') + s;
            timerEl.classList.remove('testing-timer--warning', 'testing-timer--danger');
            if (left <= 300) timerEl.classList.add('testing-timer--warning');
            if (left <= 60) timerEl.classList.add('testing-timer--danger');
        }
        updateTimer();
        setInterval(updateTimer, 1000);
    }

    // Progress bar width control (avoid inline style)
    var progressFill = document.querySelector('.testing-progress__fill');
    if (progressFill && progressFill.dataset.percent) {
        progressFill.style.width = progressFill.dataset.percent + '%';
    }
})();
