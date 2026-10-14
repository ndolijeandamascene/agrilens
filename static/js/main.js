/**
 * AgriLens Master Client Script
 * Rwanda Agricultural Intelligence Hub & Decision Support
 */

document.addEventListener('DOMContentLoaded', () => {
    initMobileNavigation();
    initNotificationDismissal();
});

/**
 * Responsive Mobile Navigation Drawer
 */
function initMobileNavigation() {
    const toggleBtn = document.getElementById('mobile-sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    if (!toggleBtn || !sidebar) return;

    // Show toggle button on narrow viewports
    const checkViewport = () => {
        if (window.innerWidth <= 992) {
            toggleBtn.style.display = 'inline-flex';
        } else {
            toggleBtn.style.display = 'none';
            sidebar.classList.remove('mobile-active');
        }
    };

    window.addEventListener('resize', checkViewport);
    checkViewport();

    toggleBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        sidebar.classList.toggle('mobile-active');
    });

    // Close when tapping outside on mobile
    document.addEventListener('click', (e) => {
        if (sidebar.classList.contains('mobile-active') && !sidebar.contains(e.target) && e.target !== toggleBtn) {
            sidebar.classList.remove('mobile-active');
        }
    });
}

/**
 * Auto-dismiss flash messages after 6 seconds
 */
function initNotificationDismissal() {
    const alerts = document.querySelectorAll('.alert-box');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-6px)';
            setTimeout(() => {
                if (alert.parentNode) alert.parentNode.removeChild(alert);
            }, 400);
        }, 6000);
    });
}
