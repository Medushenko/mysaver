/**
 * Main Application Entry Point
 * Handles navigation, routing, and global state
 */

// Import modules (they self-initialize)
import './parser.js';
import './tree.js';
import './conflicts.js';
import './tasks.js';

class App {
    constructor() {
        this.currentPage = 'parser';
        this.initNavigation();
        this.initToastSystem();
        this.initMobileMenu();
    }

    initNavigation() {
        // Handle navigation buttons
        document.querySelectorAll('.nav-item').forEach(button => {
            button.addEventListener('click', () => {
                const page = button.dataset.page;
                this.navigateTo(page);
            });
        });

        // Listen for custom navigate events
        window.addEventListener('navigate', (e) => {
            const page = e.detail.page;
            this.navigateTo(page);
        });

        // Handle browser back/forward
        window.addEventListener('popstate', () => {
            const params = new URLSearchParams(window.location.search);
            const page = params.get('page') || 'parser';
            this.navigateTo(page, false);
        });
    }

    navigateTo(page, pushState = true) {
        if (page === this.currentPage) return;

        // Update active nav item
        document.querySelectorAll('.nav-item').forEach(button => {
            button.classList.toggle('active', button.dataset.page === page);
        });

        // Show/hide pages
        document.querySelectorAll('.page').forEach(section => {
            section.classList.toggle('hidden', section.id !== `page-${page}`);
            section.classList.toggle('active', section.id === `page-${page}`);
        });

        // Update page title
        const titles = {
            parser: 'Parse Links - MySaver',
            preview: 'Preview - MySaver',
            conflicts: 'Conflicts - MySaver',
            tasks: 'Tasks - MySaver',
        };
        document.title = titles[page] || 'MySaver';

        // Update URL
        if (pushState) {
            const url = new URL(window.location);
            url.searchParams.set('page', page);
            window.history.pushState({ page }, '', url);
        }

        this.currentPage = page;

        // Close mobile menu on navigation
        this.closeMobileMenu();
    }

    initToastSystem() {
        const toastContainer = document.getElementById('toast-container');

        // Listen for toast events
        window.addEventListener('toast', (e) => {
            const { message, type } = e.detail;
            this.showToast(message, type);
        });
    }

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) return;

        const toast = document.createElement('div');
        toast.className = `toast flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg max-w-sm ${this.getToastClasses(type)}`;
        
        const icon = this.getToastIcon(type);
        
        toast.innerHTML = `
            <span class="text-lg">${icon}</span>
            <span class="flex-1 text-sm font-medium">${this.escapeHtml(message)}</span>
            <button class="toast-close text-dark-400 hover:text-dark-200">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        `;

        toastContainer.appendChild(toast);

        // Close button handler
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => this.removeToast(toast));

        // Auto-remove after 5 seconds
        setTimeout(() => {
            this.removeToast(toast);
        }, 5000);
    }

    removeToast(toast) {
        toast.classList.add('hiding');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }

    getToastClasses(type) {
        const classes = {
            success: 'bg-green-900/90 text-green-100 border border-green-700',
            error: 'bg-red-900/90 text-red-100 border border-red-700',
            warning: 'bg-yellow-900/90 text-yellow-100 border border-yellow-700',
            info: 'bg-blue-900/90 text-blue-100 border border-blue-700',
        };
        return classes[type] || classes.info;
    }

    getToastIcon(type) {
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ',
        };
        return icons[type] || icons.info;
    }

    initMobileMenu() {
        const menuToggle = document.getElementById('menu-toggle');
        const sidebar = document.getElementById('sidebar');

        if (menuToggle && sidebar) {
            menuToggle.addEventListener('click', () => {
                sidebar.classList.toggle('mobile-open');
            });

            // Close menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!sidebar.contains(e.target) && !menuToggle.contains(e.target)) {
                    this.closeMobileMenu();
                }
            });
        }
    }

    closeMobileMenu() {
        const sidebar = document.getElementById('sidebar');
        sidebar?.classList.remove('mobile-open');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const app = new App();

    // Check initial page from URL
    const params = new URLSearchParams(window.location.search);
    const initialPage = params.get('page') || 'parser';
    app.navigateTo(initialPage, false);

    console.log('MySaver Frontend initialized');
});

export default App;
