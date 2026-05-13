/**
 * Conflicts Module
 * Handles conflict resolution UI and logic
 */

import api from './api.js';

class Conflicts {
    constructor() {
        this.conflicts = [];
        this.currentTaskId = null;
        this.initListeners();
    }

    initListeners() {
        const applyPolicyBtn = document.getElementById('apply-policy-btn');
        const conflictPolicySelect = document.getElementById('conflict-policy');

        if (applyPolicyBtn) {
            applyPolicyBtn.addEventListener('click', () => this.handleApplyPolicy());
        }

        // Listen for create-task events
        window.addEventListener('create-task', async (e) => {
            await this.handleCreateTask(e.detail);
        });
    }

    async handleCreateTask({ tree, stats }) {
        this.setLoading(true);

        try {
            // Create task via API
            const taskData = {
                name: `Backup Task ${new Date().toLocaleString()}`,
                description: `Backing up ${stats.fileCount} files (${this.formatBytes(stats.totalSize)})`,
                source_path: 'multiple_sources',
                destination_path: '/backup/destination',
                file_count: stats.fileCount,
                total_size_bytes: stats.totalSize,
            };

            const task = await api.createTask(taskData);
            this.currentTaskId = task.id;

            // Generate mock conflicts for demonstration
            this.generateMockConflicts(task.id);
            
            this.showToast(`Task created: ${task.id}`, 'success');
        } catch (error) {
            console.error('Create task error:', error);
            this.showToast(`Failed to create task: ${error.message}`, 'error');
            
            // For demo purposes, create a mock task ID
            this.currentTaskId = `task-${Date.now()}`;
            this.generateMockConflicts(this.currentTaskId);
        } finally {
            this.setLoading(false);
        }
    }

    generateMockConflicts(taskId) {
        // Generate mock conflicts for demonstration
        this.conflicts = [
            {
                id: `conflict-1`,
                source: {
                    path: '/source/document.pdf',
                    name: 'document.pdf',
                    size: 1024000,
                    modified: new Date('2024-01-15').toISOString()
                },
                destination: {
                    path: '/backup/document.pdf',
                    name: 'document.pdf',
                    size: 1020000,
                    modified: new Date('2024-01-10').toISOString()
                },
                action: 'pending'
            },
            {
                id: `conflict-2`,
                source: {
                    path: '/source/photo.jpg',
                    name: 'photo.jpg',
                    size: 2048000,
                    modified: new Date('2024-01-20').toISOString()
                },
                destination: {
                    path: '/backup/photo.jpg',
                    name: 'photo.jpg',
                    size: 2048000,
                    modified: new Date('2024-01-20').toISOString()
                },
                action: 'pending'
            },
            {
                id: `conflict-3`,
                source: {
                    path: '/source/report.docx',
                    name: 'report.docx',
                    size: 512000,
                    modified: new Date('2024-01-18').toISOString()
                },
                destination: {
                    path: '/backup/report.docx',
                    name: 'report.docx',
                    size: 500000,
                    modified: new Date('2024-01-12').toISOString()
                },
                action: 'pending'
            }
        ];

        this.renderConflicts();
        
        // Navigate to conflicts page
        window.dispatchEvent(new CustomEvent('navigate', { detail: { page: 'conflicts' } }));
    }

    renderConflicts() {
        const conflictsBody = document.getElementById('conflicts-body');
        const noConflicts = document.getElementById('no-conflicts');

        if (!conflictsBody) return;

        if (this.conflicts.length === 0) {
            conflictsBody.innerHTML = '';
            noConflicts?.classList.remove('hidden');
            return;
        }

        noConflicts?.classList.add('hidden');

        conflictsBody.innerHTML = this.conflicts.map(conflict => `
            <tr class="hover:bg-dark-800 transition-colors">
                <td class="py-3 pr-4">
                    <div class="text-sm">
                        <div class="font-medium text-dark-200">${this.escapeHtml(conflict.source.name)}</div>
                        <div class="text-xs text-dark-500 truncate max-w-xs">${this.escapeHtml(conflict.source.path)}</div>
                    </div>
                </td>
                <td class="py-3 pr-4">
                    <div class="text-sm">
                        <div class="font-medium text-dark-200">${this.escapeHtml(conflict.destination.name)}</div>
                        <div class="text-xs text-dark-500 truncate max-w-xs">${this.escapeHtml(conflict.destination.path)}</div>
                    </div>
                </td>
                <td class="py-3 pr-4 text-sm text-dark-400">
                    ${this.formatBytes(conflict.source.size)}
                </td>
                <td class="py-3 pr-4 text-sm text-dark-400">
                    ${this.formatDate(conflict.source.modified)}
                </td>
                <td class="py-3">
                    <select 
                        data-conflict-id="${conflict.id}"
                        class="conflict-action bg-dark-900 border border-dark-700 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    >
                        <option value="skip" ${conflict.action === 'skip' ? 'selected' : ''}>Skip</option>
                        <option value="overwrite" ${conflict.action === 'overwrite' ? 'selected' : ''}>Overwrite</option>
                        <option value="keep_both" ${conflict.action === 'keep_both' ? 'selected' : ''}>Keep Both</option>
                        <option value="rename" ${conflict.action === 'rename' ? 'selected' : ''}>Rename</option>
                    </select>
                </td>
            </tr>
        `).join('');

        // Add listeners to action selects
        document.querySelectorAll('.conflict-action').forEach(select => {
            select.addEventListener('change', (e) => {
                const conflictId = e.target.dataset.conflictId;
                const action = e.target.value;
                this.updateConflictAction(conflictId, action);
            });
        });
    }

    updateConflictAction(conflictId, action) {
        const conflict = this.conflicts.find(c => c.id === conflictId);
        if (conflict) {
            conflict.action = action;
        }
    }

    async handleApplyPolicy() {
        const policySelect = document.getElementById('conflict-policy');
        const defaultPolicy = policySelect?.value || 'skip';

        if (!this.currentTaskId) {
            this.showToast('No active task', 'warning');
            return;
        }

        this.setLoading(true);

        try {
            // Apply default policy to all conflicts without specific action
            const conflictsToResolve = this.conflicts.filter(c => c.action === 'pending');
            
            // Update all pending conflicts with default policy
            conflictsToResolve.forEach(conflict => {
                conflict.action = defaultPolicy;
            });

            // In production, call API to apply policy
            // await api.applyConflictPolicy(this.currentTaskId, defaultPolicy);

            // Re-render with updated actions
            this.renderConflicts();

            // Show resolution report
            this.showResolutionReport(defaultPolicy);

            this.showToast(`Applied "${defaultPolicy}" policy to ${conflictsToResolve.length} conflict(s)`, 'success');
        } catch (error) {
            console.error('Apply policy error:', error);
            this.showToast(`Failed to apply policy: ${error.message}`, 'error');
        } finally {
            this.setLoading(false);
        }
    }

    showResolutionReport(defaultPolicy) {
        const reportContainer = document.getElementById('resolution-report');
        const reportContent = document.getElementById('report-content');

        if (!reportContainer || !reportContent) return;

        const stats = {
            skipped: this.conflicts.filter(c => c.action === 'skip').length,
            overwritten: this.conflicts.filter(c => c.action === 'overwrite').length,
            keepBoth: this.conflicts.filter(c => c.action === 'keep_both').length,
            renamed: this.conflicts.filter(c => c.action === 'rename').length,
        };

        reportContent.innerHTML = `
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-2">
                <div class="bg-yellow-900/30 rounded-lg p-3">
                    <div class="text-2xl font-bold text-yellow-400">${stats.skipped}</div>
                    <div class="text-xs text-yellow-500">Skipped</div>
                </div>
                <div class="bg-red-900/30 rounded-lg p-3">
                    <div class="text-2xl font-bold text-red-400">${stats.overwritten}</div>
                    <div class="text-xs text-red-500">Overwritten</div>
                </div>
                <div class="bg-blue-900/30 rounded-lg p-3">
                    <div class="text-2xl font-bold text-blue-400">${stats.keepBoth}</div>
                    <div class="text-xs text-blue-500">Keep Both</div>
                </div>
                <div class="bg-green-900/30 rounded-lg p-3">
                    <div class="text-2xl font-bold text-green-400">${stats.renamed}</div>
                    <div class="text-xs text-green-500">Renamed</div>
                </div>
            </div>
            <p class="mt-4 text-xs text-dark-500">
                Policy applied: <span class="font-medium text-dark-300">${defaultPolicy}</span>
            </p>
        `;

        reportContainer.classList.remove('hidden');

        // Navigate to tasks page after showing report
        setTimeout(() => {
            window.dispatchEvent(new CustomEvent('navigate', { detail: { page: 'tasks' } }));
        }, 2000);
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

    formatDate(isoString) {
        const date = new Date(isoString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    getConflicts() {
        return this.conflicts;
    }
}

// Initialize conflicts module
const conflicts = new Conflicts();
export default conflicts;
export { Conflicts };
