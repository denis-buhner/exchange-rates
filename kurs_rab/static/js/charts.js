function sendData(formElement, containerId = 'chart-container') {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.style.opacity = '0.5';
    const formData = new FormData(formElement);
    const params = new URLSearchParams(formData);
    fetch(`?${params.toString()}`, {
        headers: { 'x-requested-with': 'XMLHttpRequest' }
    })
    .then(response => response.text())
    .then(html => {
        container.innerHTML = html;
        container.style.opacity = '1';
        const scripts = container.querySelectorAll("script");
        scripts.forEach(oldScript => {
            const newScript = document.createElement("script");
            newScript.text = oldScript.text;
            oldScript.parentNode.replaceChild(newScript, oldScript);
        });
    })
    .catch(error => console.error('Ошибка AJAX:', error));
}
function initFilterForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            sendData(this);
        });
        form.addEventListener('change', function() {
            sendData(this);
        });
    }
}