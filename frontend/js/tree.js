/**
 * Tree Module
 * Handles preview tree rendering and interactions
 */

import api from './api.js';

class Tree {
    constructor() {
        this.treeData = null;
        this.selectedNodes = new Set();
        this.initListeners();
    }

    initListeners() {
        const selectAllBtn = document.getElementById('select-all-btn');
        const deselectAllBtn = document.getElementById('deselect-all-btn');
        const filesOnlyBtn = document.getElementById('files-only-btn');
        const createTaskBtn = document.getElementById('create-task-btn');

        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => this.selectAll());
        }

        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', () => this.deselectAll());
        }

        if (filesOnlyBtn) {
            filesOnlyBtn.addEventListener('click', () => this.selectFilesOnly());
        }

        if (createTaskBtn) {
            createTaskBtn.addEventListener('click', () => this.handleCreateTask());
        }

        // Listen for load-preview events
        window.addEventListener('load-preview', (e) => {
            this.loadPreview(e.detail.links);
        });
    }

    async loadPreview(links) {
        this.setLoading(true);

        try {
            // For now, we'll create a mock tree structure
            // In production, this would call the actual API
            const mockTree = this.createMockTree(links);
            this.treeData = mockTree;
            
            this.renderTree();
            this.updateStats();
            
            this.showToast('Preview loaded successfully', 'success');
        } catch (error) {
            console.error('Load preview error:', error);
            this.showToast(`Failed to load preview: ${error.message}`, 'error');
        } finally {
            this.setLoading(false);
        }
    }

    createMockTree(links) {
        // Create a mock tree structure for demonstration
        const root = {
            id: 'root',
            name: 'Selected Links',
            type: 'folder',
            size: 0,
            checked: true,
            children: []
        };

        links.forEach((link, index) => {
            const node = {
                id: `link-${index}`,
                name: this.extractNameFromUrl(link.url),
                type: link.type,
                size: Math.floor(Math.random() * 10000000), // Mock size
                checked: true,
                url: link.url,
                provider: link.provider,
                children: link.type === 'folder' ? this.createMockFolderContents(link.url) : []
            };
            root.children.push(node);
        });

        return root;
    }

    createMockFolderContents(url) {
        // Create mock folder contents
        const items = [];
        const fileCount = Math.floor(Math.random() * 5) + 2;

        for (let i = 0; i < fileCount; i++) {
            const isFile = Math.random() > 0.3;
            items.push({
                id: `file-${url}-${i}`,
                name: isFile ? `document_${i}.pdf` : `subfolder_${i}`,
                type: isFile ? 'file' : 'folder',
                size: isFile ? Math.floor(Math.random() * 5000000) : 0,
                checked: true,
                children: !isFile ? this.createMockFolderContents(`${url}/sub${i}`) : []
            });
        }

        return items;
    }

    extractNameFromUrl(url) {
        try {
            const urlObj = new URL(url);
            const pathParts = urlObj.pathname.split('/').filter(p => p);
            return pathParts[pathParts.length - 1] || urlObj.hostname;
        } catch {
            return url;
        }
    }

    renderTree() {
        const treeRoot = document.getElementById('tree-root');
        if (!treeRoot || !this.treeData) return;

        treeRoot.innerHTML = '';
        const nodeElement = this.renderNode(this.treeData, 0);
        treeRoot.appendChild(nodeElement);
    }

    renderNode(node, depth = 0) {
        const container = document.createElement('div');
        container.className = 'tree-node';
        
        const paddingLeft = depth * 24;
        container.style.paddingLeft = `${paddingLeft}px`;

        const hasChildren = node.children && node.children.length > 0;
        const isFolder = node.type === 'folder';

        container.innerHTML = `
            <div class="flex items-center gap-3 py-2 px-3 rounded-lg hover:bg-dark-800 transition-colors">
                <input 
                    type="checkbox" 
                    data-node-id="${node.id}"
                    ${node.checked ? 'checked' : ''}
                    class="tree-checkbox"
                >
                <button 
                    class="toggle-children ${!hasChildren ? 'invisible' : ''}"
                    data-node-id="${node.id}"
                >
                    <svg class="w-4 h-4 transform transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                    </svg>
                </button>
                <span class="file-icon ${isFolder ? 'file-icon-folder' : 'file-icon-file'}">
                    ${isFolder ? '📁' : '📄'}
                </span>
                <span class="flex-1 text-sm truncate">${this.escapeHtml(node.name)}</span>
                ${node.size > 0 ? `<span class="text-xs text-dark-500">${this.formatBytes(node.size)}</span>` : ''}
            </div>
            ${hasChildren ? `<div class="tree-children" data-parent-id="${node.id}"></div>` : ''}
        `;

        // Render children
        if (hasChildren) {
            const childrenContainer = container.querySelector('.tree-children');
            node.children.forEach(child => {
                const childElement = this.renderNode(child, depth + 1);
                childrenContainer.appendChild(childElement);
            });
        }

        // Add event listeners
        const checkbox = container.querySelector('.tree-checkbox');
        checkbox?.addEventListener('change', (e) => {
            this.handleCheckboxChange(node.id, e.target.checked);
        });

        const toggleBtn = container.querySelector('.toggle-children');
        toggleBtn?.addEventListener('click', () => {
            this.toggleChildren(node.id);
        });

        // Auto-expand root level
        if (depth === 0 && hasChildren) {
            setTimeout(() => this.toggleChildren(node.id), 0);
        }

        return container;
    }

    handleCheckboxChange(nodeId, checked) {
        this.updateNodeChecked(nodeId, checked);
        this.updateParentCheckboxes(nodeId);
        this.updateStats();
    }

    updateNodeChecked(nodeId, checked, node = this.treeData) {
        if (!node) return;

        if (node.id === nodeId) {
            node.checked = checked;
        }

        if (node.children) {
            node.children.forEach(child => {
                child.checked = checked;
                this.updateNodeChecked(nodeId, checked, child);
            });
        }
    }

    updateParentCheckboxes(nodeId, node = this.treeData, parent = null) {
        if (!node) return;

        if (node.id === nodeId && parent) {
            // Update parent checkbox based on children
            const allChildrenChecked = parent.children.every(child => child.checked);
            parent.checked = allChildrenChecked;
            this.updateParentCheckboxes(parent.id, this.treeData, null);
        }

        if (node.children) {
            node.children.forEach(child => {
                this.updateParentCheckboxes(nodeId, child, node);
            });
        }
    }

    toggleChildren(nodeId) {
        const childrenContainer = document.querySelector(`.tree-children[data-parent-id="${nodeId}"]`);
        const toggleBtn = document.querySelector(`.toggle-children[data-node-id="${nodeId}"] svg`);
        
        if (childrenContainer) {
            childrenContainer.classList.toggle('expanded');
        }
        
        if (toggleBtn) {
            toggleBtn.classList.toggle('rotate-90');
        }
    }

    selectAll() {
        this.setAllChecked(true);
        this.renderTree();
        this.updateStats();
        this.showToast('All items selected', 'info');
    }

    deselectAll() {
        this.setAllChecked(false);
        this.renderTree();
        this.updateStats();
        this.showToast('All items deselected', 'info');
    }

    selectFilesOnly() {
        this.deselectAllNodes();
        this.selectFilesRecursively(this.treeData);
        this.renderTree();
        this.updateStats();
        this.showToast('Only files selected', 'info');
    }

    setAllChecked(checked) {
        this.setCheckedRecursively(this.treeData, checked);
    }

    setCheckedRecursively(node, checked) {
        if (!node) return;
        node.checked = checked;
        if (node.children) {
            node.children.forEach(child => this.setCheckedRecursively(child, checked));
        }
    }

    deselectAllNodes() {
        this.setCheckedRecursively(this.treeData, false);
    }

    selectFilesRecursively(node) {
        if (!node) return;
        
        if (node.type === 'file') {
            node.checked = true;
        }
        
        if (node.children) {
            node.children.forEach(child => this.selectFilesRecursively(child));
        }
    }

    updateStats() {
        const stats = this.calculateStats(this.treeData);
        
        const filesCountEl = document.getElementById('selected-files-count');
        const sizeEl = document.getElementById('selected-size');
        
        if (filesCountEl) {
            filesCountEl.textContent = stats.fileCount;
        }
        
        if (sizeEl) {
            sizeEl.textContent = this.formatBytes(stats.totalSize);
        }
    }

    calculateStats(node) {
        if (!node) return { fileCount: 0, totalSize: 0 };
        
        let fileCount = 0;
        let totalSize = 0;
        
        if (node.checked && node.type === 'file') {
            fileCount++;
            totalSize += node.size || 0;
        }
        
        if (node.children) {
            node.children.forEach(child => {
                const childStats = this.calculateStats(child);
                fileCount += childStats.fileCount;
                totalSize += childStats.totalSize;
            });
        }
        
        return { fileCount, totalSize };
    }

    handleCreateTask() {
        if (!this.treeData) {
            this.showToast('No preview data available', 'warning');
            return;
        }

        const stats = this.calculateStats(this.treeData);
        if (stats.fileCount === 0) {
            this.showToast('Please select at least one file', 'warning');
            return;
        }

        // Navigate to conflicts page
        window.dispatchEvent(new CustomEvent('navigate', { detail: { page: 'conflicts' } }));
        
        // Trigger task creation
        window.dispatchEvent(new CustomEvent('create-task', {
            detail: {
                tree: this.treeData,
                stats: stats
            }
        }));

        this.showToast(`Creating task with ${stats.fileCount} files`, 'success');
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

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    getTreeData() {
        return this.treeData;
    }
}

// Initialize tree module
const tree = new Tree();
export default tree;
export { Tree };
