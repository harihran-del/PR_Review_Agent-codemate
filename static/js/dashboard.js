// Dashboard functionality for PR Review Agent
class ReviewDashboard {
    constructor() {
        this.history = this.loadHistory();
        this.init();
    }

    init() {
        this.renderStats();
        this.renderRecentReviews();
        this.setupEventListeners();
    }

    loadHistory() {
        try {
            return JSON.parse(localStorage.getItem('reviewHistory')) || [];
        } catch (error) {
            console.error('Error loading review history:', error);
            return [];
        }
    }

    saveHistory() {
        try {
            localStorage.setItem('reviewHistory', JSON.stringify(this.history));
        } catch (error) {
            console.error('Error saving review history:', error);
        }
    }

    addReview(reviewData) {
        // Keep only last 20 reviews
        this.history.unshift(reviewData);
        this.history = this.history.slice(0, 20);
        this.saveHistory();
        this.renderStats();
        this.renderRecentReviews();
    }

    renderStats() {
        const statsContainer = document.getElementById('dashboard-stats');
        if (!statsContainer) return;

        const totalReviews = this.history.length;
        const avgScore = this.history.reduce((sum, review) => {
            return sum + ((review.metrics && review.metrics.score) || 0);
        }, 0) / (totalReviews || 1);

        const totalSuggestions = this.history.reduce((sum, review) => {
            return sum + ((review.metrics && review.metrics.suggestions_count) || 0);
        }, 0);

        statsContainer.innerHTML = `
            <div class="stat-card">
                <div class="stat-number">${totalReviews}</div>
                <div class="stat-label">Total Reviews</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${Math.round(avgScore)}</div>
                <div class="stat-label">Avg Score</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${totalSuggestions}</div>
                <div class="stat-label">Suggestions</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${this.countProviders()}</div>
                <div class="stat-label">Platforms</div>
            </div>
        `;
    }

    countProviders() {
        const providers = new Set();
        this.history.forEach(review => {
            if (review.metadata && review.metadata.provider) {
                providers.add(review.metadata.provider);
            }
        });
        return providers.size;
    }

    renderRecentReviews() {
        const container = document.getElementById('recent-reviews');
        if (!container) return;

        if (this.history.length === 0) {
            container.innerHTML = '<div class="empty-state">No reviews yet. Analyze a PR to get started!</div>';
            return;
        }

        container.innerHTML = this.history.slice(0, 5).map(review => {
            const provider = (review.metadata && review.metadata.provider) || 'unknown';
            const title = (review.metadata && review.metadata.title) || review.pr_url;
            const score = (review.metrics && review.metrics.score) || 'N/A';
            const suggestions = (review.metrics && review.metrics.suggestions_count) || 0;

            return `
            <div class="review-item">
                <div class="review-item-header">
                    <span class="provider-badge">${this.getProviderIcon(provider)} ${provider}</span>
                    <span class="score">⭐ ${score}/100</span>
                </div>
                <div class="review-item-title" title="${title}">
                    ${this.truncate(title, 60)}
                </div>
                <div class="review-item-meta">
                    <span>${new Date(review.timestamp).toLocaleDateString()}</span>
                    <span>•</span>
                    <span>${suggestions} suggestions</span>
                </div>
            </div>
            `;
        }).join('');
    }

    getProviderIcon(provider) {
        const icons = {
            github: '🐙',
            gitlab: '🦊',
            bitbucket: '🪣'
        };
        return icons[provider] || '📁';
    }

    truncate(text, length) {
        return text.length > length ? text.substring(0, length) + '...' : text;
    }

    setupEventListeners() {
        // Export functionality
        const exportBtn = document.getElementById('export-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportHistory());
        }

        // Clear history
        const clearBtn = document.getElementById('clear-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearHistory());
        }
    }

    exportHistory() {
        const data = JSON.stringify(this.history, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `pr-reviews-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    clearHistory() {
        if (confirm('Are you sure you want to clear all review history?')) {
            this.history = [];
            this.saveHistory();
            this.renderStats();
            this.renderRecentReviews();
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.reviewDashboard = new ReviewDashboard();
});