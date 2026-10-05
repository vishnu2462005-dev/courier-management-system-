// Create container if it doesn't exist
function initNotifications() {
    if (!document.querySelector('.notification-container')) {
        const container = document.createElement('div');
        container.className = 'notification-container';
        document.body.appendChild(container); // Append to body to ensure it's always top-level
    }
}

// Function to show notification
function showNotification(title, message, type = 'info') {
    initNotifications();
    const container = document.querySelector('.notification-container');

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `notification-toast ${type}`;

    // Determine icon based on type
    let iconClass = 'fa-info-circle';
    if (type === 'success') iconClass = 'fa-check-circle';
    if (type === 'error') iconClass = 'fa-exclamation-circle';

    toast.innerHTML = `
        <i class="fas ${iconClass}" style="margin-top: 3px; color: ${type === 'success' ? '#22c55e' : (type === 'error' ? '#ef4444' : 'var(--accent)')}"></i>
        <div class="notification-content">
            <div class="notification-title">${title}</div>
            <div class="notification-message">${message}</div>
        </div>
        <button class="notification-close">&times;</button>
    `;

    // Close button logic
    const closeBtn = toast.querySelector('.notification-close');
    closeBtn.onclick = () => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    };

    container.appendChild(toast);

    // Trigger animation
    requestAnimationFrame(() => {
        toast.classList.add('show');
    });

    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentElement) {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }
    }, 5000);
}

// Override default window.alert for quick integration (optional, but safer to use explicit calls)
// Let's create a global helper instead to keep it clean.
window.notify = {
    success: (msg) => showNotification('Success', msg, 'success'),
    error: (msg) => showNotification('Error', msg, 'error'),
    info: (msg) => showNotification('Info', msg, 'info')
};
