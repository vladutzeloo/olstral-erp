/**
 * Universal Autocomplete Search Component
 *
 * Provides standardized search functionality with dropdown for all forms
 *
 * Usage:
 *   const search = new AutocompleteSearch({
 *       inputElement: document.querySelector('.item-search'),
 *       resultsElement: document.querySelector('.search-results'),
 *       hiddenInputElement: document.querySelector('.item-id'),
 *       searchUrl: '/items/search',
 *       minChars: 2,
 *       debounceMs: 300,
 *       onSelect: function(item) { console.log('Selected:', item); }
 *   });
 */

class AutocompleteSearch {
    constructor(options) {
        this.input = options.inputElement;
        this.results = options.resultsElement;
        this.hiddenInput = options.hiddenInputElement;
        this.searchUrl = options.searchUrl;
        this.minChars = options.minChars || 2;
        this.debounceMs = options.debounceMs || 300;
        this.onSelect = options.onSelect || function() {};
        this.searchTimeout = null;

        this.init();
    }

    init() {
        // Bind input event
        this.input.addEventListener('input', (e) => {
            this.handleInput(e.target.value);
        });

        // Hide results when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.input.contains(e.target) && !this.results.contains(e.target)) {
                this.hideResults();
            }
        });

        // Handle keyboard navigation
        this.input.addEventListener('keydown', (e) => {
            this.handleKeyboard(e);
        });
    }

    handleInput(query) {
        clearTimeout(this.searchTimeout);

        query = query.trim();

        if (query.length < this.minChars) {
            this.hideResults();
            this.hiddenInput.value = '';
            return;
        }

        this.searchTimeout = setTimeout(() => {
            this.performSearch(query);
        }, this.debounceMs);
    }

    async performSearch(query) {
        try {
            const response = await fetch(`${this.searchUrl}?q=${encodeURIComponent(query)}`);
            const items = await response.json();

            this.displayResults(items);
        } catch (error) {
            console.error('Search error:', error);
            this.showError('Error performing search');
        }
    }

    displayResults(items) {
        if (items.length === 0) {
            this.results.innerHTML = '<div class="no-results">No items found</div>';
            this.showResults();
            return;
        }

        this.results.innerHTML = items.map(item =>
            `<div class="result-item" data-id="${item.id}" data-label="${item.label}">
                ${item.label}
            </div>`
        ).join('');

        // Attach click handlers
        this.results.querySelectorAll('.result-item').forEach(div => {
            div.addEventListener('click', () => {
                this.selectItem({
                    id: div.dataset.id,
                    label: div.dataset.label
                });
            });
        });

        this.showResults();
    }

    selectItem(item) {
        this.hiddenInput.value = item.id;
        this.input.value = item.label;
        this.hideResults();
        this.onSelect(item);
    }

    showResults() {
        this.results.style.display = 'block';
    }

    hideResults() {
        this.results.style.display = 'none';
    }

    showError(message) {
        this.results.innerHTML = `<div class="error-message">${message}</div>`;
        this.showResults();
    }

    handleKeyboard(e) {
        const items = this.results.querySelectorAll('.result-item');
        if (items.length === 0) return;

        const currentActive = this.results.querySelector('.result-item.active');
        let currentIndex = currentActive ? Array.from(items).indexOf(currentActive) : -1;

        switch(e.key) {
            case 'ArrowDown':
                e.preventDefault();
                currentIndex = Math.min(currentIndex + 1, items.length - 1);
                this.setActiveItem(items, currentIndex);
                break;
            case 'ArrowUp':
                e.preventDefault();
                currentIndex = Math.max(currentIndex - 1, 0);
                this.setActiveItem(items, currentIndex);
                break;
            case 'Enter':
                e.preventDefault();
                if (currentActive) {
                    currentActive.click();
                }
                break;
            case 'Escape':
                this.hideResults();
                break;
        }
    }

    setActiveItem(items, index) {
        items.forEach(item => item.classList.remove('active'));
        if (index >= 0 && index < items.length) {
            items[index].classList.add('active');
            items[index].scrollIntoView({ block: 'nearest' });
        }
    }

    // Public method to clear the search
    clear() {
        this.input.value = '';
        this.hiddenInput.value = '';
        this.hideResults();
    }
}

/**
 * Initialize all autocomplete search inputs on a page
 *
 * Usage:
 *   Add data attributes to your HTML:
 *   <input type="text" class="autocomplete-search"
 *          data-search-url="/items/search"
 *          data-target-id="item-id-input">
 *   <input type="hidden" id="item-id-input">
 *   <div class="search-results"></div>
 */
function initializeAutocompleteSearches() {
    document.querySelectorAll('.autocomplete-search').forEach(input => {
        const container = input.closest('.autocomplete-container');
        if (!container) {
            console.warn('Autocomplete input must be inside .autocomplete-container', input);
            return;
        }

        const resultsDiv = container.querySelector('.search-results');
        const hiddenInput = document.getElementById(input.dataset.targetId);

        if (!resultsDiv || !hiddenInput) {
            console.warn('Missing results div or hidden input for autocomplete', input);
            return;
        }

        new AutocompleteSearch({
            inputElement: input,
            resultsElement: resultsDiv,
            hiddenInputElement: hiddenInput,
            searchUrl: input.dataset.searchUrl,
            minChars: parseInt(input.dataset.minChars || '2'),
            debounceMs: parseInt(input.dataset.debounceMs || '300')
        });
    });
}

// Auto-initialize on DOM load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAutocompleteSearches);
} else {
    initializeAutocompleteSearches();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AutocompleteSearch;
}
