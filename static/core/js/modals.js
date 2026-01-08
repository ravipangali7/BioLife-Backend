/**
 * Modal Manager - Centralized modal management for admin panel
 * Handles initialization, form submission, validation, and animations
 */

class ModalManager {
    constructor() {
        this.modals = new Map();
        this.initialized = false;
        this.init();
    }

    /**
     * Initialize all modals on the page
     */
    init() {
        if (this.initialized) return;
        
        // Wait for DOM and Bootstrap to be ready
        const initModals = () => {
            // Check if Bootstrap is available
            if (typeof bootstrap === 'undefined' || !bootstrap.Modal) {
                // Retry after a short delay
                setTimeout(initModals, 100);
                return;
            }
            
            this.setupModals();
            this.initialized = true;
        };
        
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initModals);
        } else {
            initModals();
        }
    }

    /**
     * Setup event listeners for all modals
     */
    setupModals() {
        // Check if Bootstrap is available
        if (typeof bootstrap === 'undefined' || !bootstrap.Modal) {
            console.warn('Bootstrap Modal not found. Modals may not work correctly.');
            return;
        }
        
        // Find all modals on the page
        const modalElements = document.querySelectorAll('.modal');
        
        modalElements.forEach(modal => {
            const modalId = modal.id;
            if (!modalId) return;
            
            // Move modal to body if it's inside a container (ensures absolute positioning works)
            // Bootstrap does this automatically, but we ensure it happens
            if (modal.parentElement && modal.parentElement.tagName !== 'BODY') {
                // Store original parent for reference
                modal.dataset.originalParent = modal.parentElement.className || '';
            }
            
            // Store modal reference
            this.modals.set(modalId, modal);
            
            // Get or create Bootstrap modal instance
            let bsModal;
            try {
                bsModal = bootstrap.Modal.getOrCreateInstance(modal, {
                    backdrop: true,
                    keyboard: true,
                    focus: true
                });
            } catch (e) {
                console.warn(`Failed to initialize modal ${modalId}:`, e);
                return;
            }
            
            // Setup event listeners
            this.setupModalEvents(modal, bsModal);
        });
    }

    /**
     * Setup event listeners for a specific modal
     */
    setupModalEvents(modal, bsModal) {
        const modalId = modal.id;
        
        // When modal is about to be shown
        modal.addEventListener('show.bs.modal', (e) => {
            this.onModalShow(modal, e);
        });
        
        // When modal is shown
        modal.addEventListener('shown.bs.modal', (e) => {
            this.onModalShown(modal, e);
        });
        
        // When modal is about to be hidden
        modal.addEventListener('hide.bs.modal', (e) => {
            this.onModalHide(modal, e);
        });
        
        // When modal is hidden
        modal.addEventListener('hidden.bs.modal', (e) => {
            this.onModalHidden(modal, e);
        });
        
        // Handle form submissions within modal
        const form = modal.querySelector('form');
        if (form) {
            this.setupFormSubmission(form, modal, bsModal);
        }
    }

    /**
     * Handle modal show event
     */
    onModalShow(modal, e) {
        // Add animation classes
        const dialog = modal.querySelector('.modal-dialog');
        if (dialog) {
            dialog.classList.add('modal-slide-up');
        }
        
        // Reset form if exists
        const form = modal.querySelector('form');
        if (form) {
            form.reset();
            // Clear validation classes
            const inputs = form.querySelectorAll('.form-control, .form-select');
            inputs.forEach(input => {
                input.classList.remove('is-invalid', 'is-valid');
            });
            // Clear error messages
            const errorMessages = form.querySelectorAll('.invalid-feedback');
            errorMessages.forEach(msg => msg.remove());
        }
        
        // Reset button states
        const submitButtons = modal.querySelectorAll('button[type="submit"]');
        submitButtons.forEach(btn => {
            btn.classList.remove('loading');
            btn.disabled = false;
        });
    }

    /**
     * Handle modal shown event
     */
    onModalShown(modal, e) {
        // Re-initialize Feather icons
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
        
        // Focus first input if exists
        const firstInput = modal.querySelector('input:not([type="hidden"]), textarea, select');
        if (firstInput && firstInput.type !== 'file') {
            setTimeout(() => firstInput.focus(), 100);
        }
    }

    /**
     * Handle modal hide event
     */
    onModalHide(modal, e) {
        // Remove animation classes
        const dialog = modal.querySelector('.modal-dialog');
        if (dialog) {
            dialog.classList.remove('modal-slide-up');
        }
    }

    /**
     * Handle modal hidden event
     */
    onModalHidden(modal, e) {
        // Clean up any temporary elements
        const loadingButtons = modal.querySelectorAll('.btn.loading');
        loadingButtons.forEach(btn => {
            btn.classList.remove('loading');
            btn.disabled = false;
        });
    }

    /**
     * Setup form submission handling
     */
    setupFormSubmission(form, modal, bsModal) {
        // Skip handling if form has data-no-modal-handler attribute
        if (form.dataset.noModalHandler === 'true') {
            return; // Allow normal form submission
        }
        
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Validate form
            if (!this.validateForm(form)) {
                return false;
            }
            
            // Show loading state
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.classList.add('loading');
                submitButton.disabled = true;
            }
            
            // Disable all form inputs during submission
            const inputs = form.querySelectorAll('input, textarea, select, button');
            inputs.forEach(input => {
                input.disabled = true;
            });
            
            // Submit form via fetch or allow default submission
            // For now, we'll allow default submission but add loading state
            // You can customize this to use fetch API if needed
            
            // Re-enable inputs after a delay (in case of error)
            setTimeout(() => {
                if (submitButton && submitButton.classList.contains('loading')) {
                    submitButton.classList.remove('loading');
                    submitButton.disabled = false;
                    inputs.forEach(input => {
                        input.disabled = false;
                    });
                }
            }, 5000);
            
            // Submit the form
            form.submit();
        });
    }

    /**
     * Validate form before submission
     */
    validateForm(form) {
        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');
        
        requiredFields.forEach(field => {
            // Remove previous validation classes
            field.classList.remove('is-invalid', 'is-valid');
            
            // Remove previous error messages
            const existingError = field.parentElement.querySelector('.invalid-feedback');
            if (existingError) {
                existingError.remove();
            }
            
            // Validate field
            if (!field.value.trim()) {
                isValid = false;
                field.classList.add('is-invalid');
                
                // Add error message
                const errorDiv = document.createElement('div');
                errorDiv.className = 'invalid-feedback';
                errorDiv.textContent = 'This field is required.';
                field.parentElement.appendChild(errorDiv);
            } else {
                field.classList.add('is-valid');
            }
        });
        
        // Scroll to first invalid field
        if (!isValid) {
            const firstInvalid = form.querySelector('.is-invalid');
            if (firstInvalid) {
                firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstInvalid.focus();
            }
        }
        
        return isValid;
    }

    /**
     * Show a modal programmatically
     */
    show(modalId) {
        const modal = this.modals.get(modalId);
        if (modal) {
            const bsModal = bootstrap.Modal.getOrCreateInstance(modal);
            bsModal.show();
        }
    }

    /**
     * Hide a modal programmatically
     */
    hide(modalId) {
        const modal = this.modals.get(modalId);
        if (modal) {
            const bsModal = bootstrap.Modal.getOrCreateInstance(modal);
            bsModal.hide();
        }
    }

    /**
     * Toggle a modal
     */
    toggle(modalId) {
        const modal = this.modals.get(modalId);
        if (modal) {
            const bsModal = bootstrap.Modal.getOrCreateInstance(modal);
            bsModal.toggle();
        }
    }
}

// Initialize ModalManager when DOM and Bootstrap are ready
let modalManager;

function initializeModalManager() {
    // Wait for Bootstrap to be available
    if (typeof bootstrap === 'undefined' || !bootstrap.Modal) {
        // Retry after a short delay
        setTimeout(initializeModalManager, 100);
        return;
    }
    
    modalManager = new ModalManager();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeModalManager);
} else {
    initializeModalManager();
}

// Make ModalManager available globally
window.ModalManager = ModalManager;
window.modalManager = modalManager;

