/**
 * Utility functions for the Text Chunk Visualizer
 * Reduces conditional checks and provides helper methods
 */

/**
 * Safely get an element or return null
 * @param {string} id - Element ID
 * @returns {HTMLElement|null}
 */
function getElement(id) {
    return document.getElementById(id) || null;
}

/**
 * Safely set element text content
 * @param {HTMLElement|null} element - Element to modify
 * @param {string} text - Text content to set
 */
function setElementText(element, text) {
    if (element) {
        element.textContent = text;
    }
}

/**
 * Safely set element HTML content
 * @param {HTMLElement|null} element - Element to modify
 * @param {string} html - HTML content to set
 */
function setElementHTML(element, html) {
    if (element) {
        element.innerHTML = html;
    }
}

/**
 * Safely toggle element class
 * @param {HTMLElement|null} element - Element to modify
 * @param {string} className - Class to toggle
 * @param {boolean} force - Force add/remove (optional)
 */
function toggleElementClass(element, className, force) {
    if (element) {
        element.classList.toggle(className, force);
    }
}

/**
 * Safely add event listener to element
 * @param {HTMLElement|null} element - Element to add listener to
 * @param {string} event - Event type
 * @param {Function} handler - Event handler
 */
function addElementListener(element, event, handler) {
    if (element) {
        element.addEventListener(event, handler);
    }
}

/**
 * Safely set element disabled state
 * @param {HTMLElement|null} element - Element to modify
 * @param {boolean} disabled - Disabled state
 */
function setElementDisabled(element, disabled) {
    if (element) {
        element.disabled = disabled;
    }
}

/**
 * Safely set element value
 * @param {HTMLElement|null} element - Element to modify
 * @param {string} value - Value to set
 */
function setElementValue(element, value) {
    if (element) {
        element.value = value;
    }
}

/**
 * Safely set element style property
 * @param {HTMLElement|null} element - Element to modify
 * @param {string} property - CSS property name
 * @param {string} value - CSS value
 */
function setElementStyle(element, property, value) {
    if (element) {
        element.style[property] = value;
    }
}

/**
 * Batch update multiple token-related elements
 * @param {Object} elements - Elements object
 * @param {boolean} available - Whether token counter is available
 */
function updateTokenElements(elements, available) {
    const tokenElements = [
        'max_tokens', 'max_tokens_hint', 
        'max_tokens_code', 'max_tokens_code_hint'
    ];
    
    tokenElements.forEach(elementKey => {
        const element = elements[elementKey];
        if (element) {
            if (elementKey.includes('_hint')) {
                setElementText(element, available ? 'Chunk by token count' : 'Chunk by token count (token counter not available)');
                setElementStyle(element, 'color', available ? 'var(--text-tertiary)' : 'var(--error-color)');
            } else {
                setElementDisabled(element, !available);
                if (!available) {
                    setElementValue(element, '');
                }
            }
        }
    });
}

/**
 * Format date for display
 * @param {Date} date - Date to format
 * @returns {string} Formatted date string
 */
function formatDate(date) {
    return date.toLocaleString("en-US", {
        month: "long",
        day: "2-digit", 
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: true
    });
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped HTML
 */
function escapeHtml(text) {
    if (text == null) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Check if browser supports optional chaining (?.)
 * @returns {boolean} Whether optional chaining is supported
 */
function supportsOptionalChaining() {
    try {
        return eval('({})?.test') === undefined;
    } catch {
        return false;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        getElement,
        setElementText,
        setElementHTML,
        toggleElementClass,
        addElementListener,
        setElementDisabled,
        setElementValue,
        setElementStyle,
        updateTokenElements,
        formatDate,
        escapeHtml,
        supportsOptionalChaining
    };
}