/**
 * Parser Module
 * Handles link parsing functionality
 */

import api from './api.js';

class Parser {
    constructor() {
        this.parsedLinks = [];
        this.errors = [];
        this.initListeners();
    }

    initListeners() {
        const parseBtn = document.getElementById('parse-btn');
        const clearBtn = document.getElementById('clear-btn');
        const proceedBtn = document.getElementById('proceed-preview-btn');
        const parseInput = document.getElementById('parse-input');

        if (parseBtn) {
            parseBtn.addEventListener('click', () => this.handleParse());
        }

        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.handleClear());
        }

        if (proceedBtn) {
            proceedBtn.addEventListener('click', () => this.handleProceedToPreview());
        }

        // Allow Ctrl+Enter to parse
        if (parseInput) {
            parseInput.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.key === 'Enter') {
                    this.handleParse();
                }
            });
        }
    }

    async handleParse() {
        const parseInput = document.getElementById('parse-input');
        const parseBtn = document.getElementById('parse-btn');
        const text = parseInput?.value?.trim();

        if (!text) {
            this.showToast('Please enter some text with links', 'error');
            return;
        }

        // Show loading state
        this.setLoading(true);
        parseBtn.disabled = true;

        try {
            const response = await api.parseText(text);
            
            this.parsedLinks = response.links || [];
            this.errors = response.errors || [];

            this.renderResults();
            
            if (this.parsedLinks.length > 0) {
                this.showToast(`Found ${this.parsedLinks.length} link(s)`, 'success');
            } else {
                this.showToast('No links found in the text', 'warning');
            }

            if (this.errors.length > 0) {
                this.showToast(`${this.errors.length} error(s) during parsing`, 'error');
            }
        } catch (error) {
            console.error('Parse error:', error);
            this.showToast(`Failed to parse: ${error.message}`, 'error');
            this.errors = [error.message];
        } finally {
            this.setLoading(false);
            parseBtn.disabled = false;
        }
    }

    handleClear() {
        const parseInput = document.getElementById('parse-input');
        const parseResults = document.getElementById('parse-results');
        
        if (parseInput) {
            parseInput.value = '';
        }
        
        if (parseResults) {
            parseResults.classList.add('hidden');
        }
        
        this.parsedLinks = [];
        this.errors = [];
        
        this.showToast('Cleared', 'info');
    }

    handleProceedToPreview() {
        if (this.parsedLinks.length === 0) {
            this.showToast('No links to preview', 'warning');
            return;
        }

        // Navigate to preview page
        window.dispatchEvent(new CustomEvent('navigate', { detail: { page: 'preview' } }));
        
        // Trigger preview loading
        window.dispatchEvent(new CustomEvent('load-preview', { 
            detail: { links: this.parsedLinks } 
        }));
    }

    renderResults() {
        const parseResults = document.getElementById('parse-results');
        const linksList = document.getElementById('links-list');

        if (!parseResults || !linksList) return;

        if (this.parsedLinks.length === 0) {
            parseResults.classList.add('hidden');
            return;
        }

        linksList.innerHTML = this.parsedLinks.map((link, index) => `
            <div class="bg-dark-900 rounded-lg p-4 border border-dark-700">
                <div class="flex items-start justify-between gap-4">
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2 mb-2">
                            <span class="px-2 py-1 rounded text-xs font-medium ${this.getProviderBadgeClass(link.provider)}">
                                ${this.getProviderIcon(link.provider)} ${link.provider}
                            </span>
                            <span class="px-2 py-1 rounded text-xs font-medium ${this.getTypeBadgeClass(link.type)}">
                                ${link.type}
                            </span>
                        </div>
                        <p class="text-sm text-dark-300 break-all">${this.escapeHtml(link.url)}</p>
                    </div>
                </div>
            </div>
        `).join('');

        parseResults.classList.remove('hidden');
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

    getProviderBadgeClass(provider) {
        const classes = {
            yandex: 'bg-yellow-900/50 text-yellow-400',
            google: 'bg-red-900/50 text-red-400',
            local: 'bg-green-900/50 text-green-400',
        };
        return classes[provider] || 'bg-dark-700 text-dark-300';
    }

    getTypeBadgeClass(type) {
        const classes = {
            file: 'bg-blue-900/50 text-blue-400',
            folder: 'bg-purple-900/50 text-purple-400',
        };
        return classes[type] || 'bg-dark-700 text-dark-300';
    }

    getProviderIcon(provider) {
        const icons = {
            yandex: '🟡',
            google: '🔴',
            local: '📁',
        };
        return icons[provider] || '🔗';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    getParsedLinks() {
        return this.parsedLinks;
    }
}

// Initialize parser module
const parser = new Parser();
export default parser;
export { Parser };
