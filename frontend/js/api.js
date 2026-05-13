/**
 * API Client for MySaver Backend
 * Handles all HTTP requests with error handling and retry logic
 */

class ApiClient {
    constructor() {
        this.baseUrl = this.detectBaseUrl();
        this.defaultTimeout = 30000; // 30 seconds
        this.maxRetries = 3;
    }

    /**
     * Detect base URL based on environment
     * Development: localhost:8000
     * Production: relative path /api/v1
     */
    detectBaseUrl() {
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            return 'http://localhost:8000/api/v1';
        }
        return '/api/v1';
    }

    /**
     * Generic fetch wrapper with error handling and retries
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            timeout: this.defaultTimeout,
            ...options,
        };

        let lastError;
        for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), config.timeout);

                const response = await fetch(url, {
                    ...config,
                    signal: controller.signal,
                });

                clearTimeout(timeoutId);

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
                    throw new ApiError(errorData.detail || `HTTP ${response.status}`, response.status);
                }

                // Handle no-content responses
                if (response.status === 204) {
                    return null;
                }

                return await response.json();
            } catch (error) {
                lastError = error;

                // Don't retry on client errors (4xx) or abort
                if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
                    break;
                }
                if (error.name === 'AbortError') {
                    break;
                }

                // Wait before retry (exponential backoff)
                if (attempt < this.maxRetries) {
                    await this.sleep(1000 * Math.pow(2, attempt - 1));
                }
            }
        }

        throw lastError;
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // ==================== Parser Endpoints ====================

    /**
     * Parse text for links
     * POST /parse
     */
    async parseText(text) {
        return await this.request('/parse', {
            method: 'POST',
            body: JSON.stringify({ text }),
        });
    }

    // ==================== Preview Endpoints ====================

    /**
     * Get preview tree for a task
     * GET /preview/{task_id}
     */
    async getPreview(taskId) {
        return await this.request(`/preview/${taskId}`);
    }

    // ==================== Task Endpoints ====================

    /**
     * Create a new task
     * POST /tasks
     */
    async createTask(taskData) {
        return await this.request('/tasks', {
            method: 'POST',
            body: JSON.stringify(taskData),
        });
    }

    /**
     * Get task status
     * GET /tasks/{id}
     */
    async getTaskStatus(taskId) {
        return await this.request(`/tasks/${taskId}`);
    }

    /**
     * Get all tasks
     * GET /tasks
     */
    async getAllTasks() {
        return await this.request('/tasks');
    }

    /**
     * Cancel a task
     * POST /tasks/{id}/cancel
     */
    async cancelTask(taskId) {
        return await this.request(`/tasks/${taskId}/cancel`, {
            method: 'POST',
        });
    }

    // ==================== Conflict Endpoints ====================

    /**
     * Apply conflict policy
     * POST /conflicts
     */
    async applyConflictPolicy(taskId, policy) {
        return await this.request('/conflicts', {
            method: 'POST',
            body: JSON.stringify({ task_id: taskId, policy }),
        });
    }

    /**
     * Get conflicts for a task
     * GET /conflicts/{task_id}
     */
    async getConflicts(taskId) {
        return await this.request(`/conflicts/${taskId}`);
    }

    // ==================== Report Endpoints ====================

    /**
     * Get task report
     * GET /reports/{task_id}
     */
    async getReport(taskId) {
        return await this.request(`/reports/${taskId}`);
    }

    /**
     * Send report to Telegram
     * POST /reports/{task_id}/send
     */
    async sendReportToTelegram(taskId) {
        return await this.request(`/reports/${taskId}/send`, {
            method: 'POST',
        });
    }

    // ==================== Cache Endpoints ====================

    /**
     * Clear cache
     * DELETE /cache
     */
    async clearCache(options = {}) {
        return await this.request('/cache', {
            method: 'DELETE',
            body: JSON.stringify(options),
        });
    }

    // ==================== Health Check ====================

    /**
     * Check backend health
     * GET /health
     */
    async healthCheck() {
        return await this.request('/health');
    }
}

/**
 * Custom API Error class
 */
class ApiError extends Error {
    constructor(message, status) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
    }
}

// Export singleton instance
const api = new ApiClient();
export default api;
export { ApiClient, ApiError };
