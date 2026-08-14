document.addEventListener('DOMContentLoaded', function () {
    document.body.addEventListener('htmx:responseError', function (event) {
        console.error('HTMX error:', event.detail.xhr.status, event.detail.xhr.responseText);
    });

    document.body.addEventListener('htmx:afterSwap', function (event) {
        if (event.detail.target.id === 'flash-container') {
            setTimeout(function () {
                const flashes = document.querySelectorAll('#flash-container .alert');
                flashes.forEach(function (el) {
                    const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
                    setTimeout(function () { bsAlert.close(); }, 5000);
                });
            }, 100);
        }
    });
});
