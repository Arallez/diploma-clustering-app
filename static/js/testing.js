/**
 * Testing section: timer on take-test page only.
 * No inline scripts in templates — this file runs only when included.
 */
(function() {
    var el = document.getElementById('timer');
    var form = document.getElementById('submit-test-form');
    if (!el || !el.dataset.endsAt) return;
    var endsAt = new Date(el.dataset.endsAt);

    function update() {
        var now = new Date();
        var left = Math.max(0, Math.floor((endsAt - now) / 1000));
        if (left <= 0) {
            el.textContent = 'Время вышло';
            el.classList.add('testing-timer--danger');
            if (form) form.submit();
            return;
        }
        var m = Math.floor(left / 60);
        var s = left % 60;
        el.textContent = m + ':' + (s < 10 ? '0' : '') + s;
        el.classList.remove('testing-timer--warning', 'testing-timer--danger');
        if (left <= 300) el.classList.add('testing-timer--warning');
        if (left <= 60) el.classList.add('testing-timer--danger');
    }
    update();
    setInterval(update, 1000);
})();
