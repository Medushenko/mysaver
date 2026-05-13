/**
 * Tasks Module
 * Handles task monitoring with real-time updates via polling
 */

import api from './api.js';

class Tasks {
    constructor() {
        this.tasks = [];
        this.pollingInterval = null;
        this.pollingDelay = 5000; // 5 seconds
        this.initListeners();
    }

    initListeners() {
        const refreshBtn = document.getElementById('refresh-tasks-btn');

        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadTasks());
        }

        // Auto-load tasks when navigating to tasks page
        window.addEventListener('navigate', (e) => {
            if (e.detail.page === 'tasks') {
                this.loadTasks();
                this.startPolling();
            } else {
                this.stopPolling();
            }
        });

        // Initial load
        this.loadTasks();
    }

    async loadTasks() {
        try {
            const response = await api.getAllTasks();
            this.tasks = response || [];
            this.renderTasks();
        } catch (error) {
            console.error('Load tasks error:', error);
            // For demo, create mock tasks
            this.createMockTasks();
        }
    }

    createMockTasks() {
        // Create mock tasks for demonstration
        this.tasks = [
            {
                id: `task-${Date.now() - 10000}`,
                name: 'Backup Photos',
                description: 'Backing up photo library',
                status: 'running',
                progress: 65,
                file_count: 1250,
                total_size_bytes: 5368709120,
                created_at: new Date(Date.now() - 300000).toISOString(),
                started_at: new Date(Date.now() - 280000).toISOString(),
            },
            {
                id: `task-${Date.now() - 20000}`,
                name: 'Documents Sync',
                description: 'Syncing documents folder',
                status: 'success',
                progress: 100,
                file_count: 342,
                total_size_bytes: 1073741824,
                created_at: new Date(Date.now() - 600000).toISOString(),
                started_at: new Date(Date.now() - 580000).toISOString(),
                completed_at: new Date(Date.now() - 120000).toISOString(),
            },
            {
                id: `task-${Date.now() - 30000}`,
                name: 'Video Archive',
                description: 'Archiving video files',
                status: 'pending',
                progress: 0,
                file_count: 89,
                total_size_bytes: 10737418240,
                created_at: new Date(Date.now() - 120000).toISOString(),
            }
        ];

        this.renderTasks();
    }

    renderTasks() {
        const tasksList = document.getElementById('tasks-list');
        const noTasks = document.getElementById('no-tasks');

        if (!tasksList) return;

        if (this.tasks.length === 0) {
            tasksList.innerHTML = '';
            noTasks?.classList.remove('hidden');
            return;
        }

        noTasks?.classList.add('hidden');

        tasksList.innerHTML = this.tasks.map(task => `
            <div class="bg-dark-800 rounded-xl p-6 shadow-lg border border-dark-700">
                <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                    <div class="flex-1">
                        <div class="flex items-center gap-3 mb-2">
                            <h3 class="text-lg font-semibold">${this.escapeHtml(task.name)}</h3>
                            <span class="status-badge status-${task.status}">${task.status}</span>
                        </div>
                        <p class="text-sm text-dark-400">${this.escapeHtml(task.description || '')}</p>
                    </div>
                    <div class="flex items-center gap-2">
                        ${task.status === 'running' ? `
                            <button 
                                data-task-id="${task.id}"
                                class="cancel-task-btn bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm transition-colors"
                            >
                                Cancel
                            </button>
                        ` : ''}
                        ${task.status === 'success' ? `
                            <button 
                                data-task-id="${task.id}"
                                class="view-report-btn bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg text-sm transition-colors"
                            >
                                View Report
                            </button>
                        ` : ''}
                    </div>
                </div>

                <!-- Progress Bar -->
                <div class="mb-4">
                    <div class="flex justify-between text-sm mb-2">
                        <span class="text-dark-400">Progress</span>
                        <span class="text-dark-300">${task.progress}%</span>
                    </div>
                    <div class="w-full bg-dark-900 rounded-full h-3 overflow-hidden">
                        <div 
                            class="progress-bar h-full rounded-full ${this.getProgressColorClass(task.status)}"
                            style="width: ${task.progress}%"
                        ></div>
                    </div>
                </div>

                <!-- Stats Grid -->
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                        <span class="text-dark-500">Files:</span>
                        <span class="ml-2 text-dark-200">${task.file_count || 0}</span>
                    </div>
                    <div>
                        <span class="text-dark-500">Size:</span>
                        <span class="ml-2 text-dark-200">${this.formatBytes(task.total_size_bytes || 0)}</span>
                    </div>
                    <div>
                        <span class="text-dark-500">Created:</span>
                        <span class="ml-2 text-dark-200">${this.formatDateTime(task.created_at)}</span>
                    </div>
                    ${task.completed_at ? `
                        <div>
                            <span class="text-dark-500">Completed:</span>
                            <span class="ml-2 text-dark-200">${this.formatDateTime(task.completed_at)}</span>
                        </div>
                    ` : ''}
                </div>

                <!-- Extended Info for Running Tasks -->
                ${task.status === 'running' ? `
                    <div class="mt-4 pt-4 border-t border-dark-700">
                        <div class="flex items-center gap-2 text-sm text-dark-400">
                            <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                            </svg>
                            <span>Processing...</span>
                        </div>
                    </div>
                ` : ''}
            </div>
        `).join('');

        // Add event listeners
        document.querySelectorAll('.cancel-task-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const taskId = e.target.dataset.taskId;
                this.handleCancelTask(taskId);
            });
        });

        document.querySelectorAll('.view-report-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const taskId = e.target.dataset.taskId;
                this.handleViewReport(taskId);
            });
        });
    }

    getProgressColorClass(status) {
        const classes = {
            pending: 'bg-yellow-500',
            running: 'bg-primary-500',
            success: 'bg-green-500',
            failed: 'bg-red-500',
            cancelled: 'bg-dark-500',
        };
        return classes[status] || 'bg-primary-500';
    }

    async handleCancelTask(taskId) {
        if (!confirm('Are you sure you want to cancel this task?')) {
            return;
        }

        try {
            await api.cancelTask(taskId);
            
            // Update local state
            const task = this.tasks.find(t => t.id === taskId);
            if (task) {
                task.status = 'cancelled';
                task.progress = 0;
            }

            this.renderTasks();
            this.showToast('Task cancelled', 'info');
        } catch (error) {
            console.error('Cancel task error:', error);
            this.showToast(`Failed to cancel task: ${error.message}`, 'error');
        }
    }

    async handleViewReport(taskId) {
        try {
            const report = await api.getReport(taskId);
            
            // Show report in a toast or navigate to report page
            this.showToast(`Report for task ${taskId}`, 'info');
            
            // In production, navigate to a dedicated report page
            console.log('Report:', report);
        } catch (error) {
            console.error('Get report error:', error);
            this.showToast(`Failed to load report: ${error.message}`, 'error');
        }
    }

    startPolling() {
        this.stopPolling(); // Clear existing interval
        
        this.pollingInterval = setInterval(async () => {
            await this.loadTasks();
        }, this.pollingDelay);
    }

    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }

    setLoading(isLoading) {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.toggle('hidden', !isLoading);
            overlay.classList.toggle('flex', isLoading);
        }
    }

    showToast(message, type = 'info') {
        window.dispatchEvent(new CustomEvent('toast', {
            detail: { message, type }
        }));
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    formatDateTime(isoString) {
        if (!isoString) return 'N/A';
        const date = new Date(isoString);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    getTasks() {
        return this.tasks;
    }
}

// Initialize tasks module
const tasks = new Tasks();
export default tasks;
export { Tasks };
