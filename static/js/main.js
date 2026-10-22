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
    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && window.closeAgriLensSidebar) {
            window.closeAgriLensSidebar();
        }
    });

    // Window resize check: close drawer if window expands to desktop
    window.addEventListener('resize', () => {
        if (window.innerWidth > 992 && window.closeAgriLensSidebar) {
            window.closeAgriLensSidebar();
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

