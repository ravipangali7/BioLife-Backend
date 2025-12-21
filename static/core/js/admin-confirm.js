/**
 * Admin Confirm Handler - Replaces native confirm() with SweetAlert2
 * Handles confirmation dialogs for admin actions
 */

(function() {
    'use strict';

    /**
     * Initialize confirmation handlers
     */
    function initConfirmHandlers() {
        // Wait for SweetAlert2 to be available
        if (typeof Swal === 'undefined') {
            setTimeout(initConfirmHandlers, 100);
            return;
        }

        // Handle buttons with data-confirm attribute
        document.querySelectorAll('[data-confirm]').forEach(function(element) {
            // Skip if already initialized
            if (element.dataset.confirmInitialized === 'true') {
                return;
            }
            element.dataset.confirmInitialized = 'true';

            // Determine if it's a form or button
            const isForm = element.tagName === 'FORM';
            const isButton = element.tagName === 'BUTTON' || element.tagName === 'A';

            if (isForm) {
                // Handle form submissions
                const submitHandler = function(e) {
                    // Check if this submit should bypass confirmation
                    if (element.dataset.confirmBypass === 'true') {
                        element.dataset.confirmBypass = 'false';
                        return; // Allow default submission
                    }
                    
                    e.preventDefault();
                    e.stopPropagation();
                    const form = element;
                    showConfirmation(form, function() {
                        // Set flag to bypass confirmation and submit
                        form.dataset.confirmBypass = 'true';
                        form.submit();
                    });
                };
                
                element.addEventListener('submit', submitHandler);
            } else if (isButton) {
                // Handle button clicks
                element.addEventListener('click', function(e) {
                    e.preventDefault();
                    const form = element.closest('form');
                    const href = element.href || (form ? null : null);
                    
                    showConfirmation(element, function() {
                        if (form) {
                            // If button is inside a form, submit the form
                            form.submit();
                        } else if (href) {
                            // If it's a link, navigate to href
                            window.location.href = href;
                        } else {
                            // Default: trigger click without preventDefault
                            const originalClick = new MouseEvent('click', {
                                bubbles: true,
                                cancelable: true,
                                view: window
                            });
                            element.dispatchEvent(originalClick);
                        }
                    });
                });
            }
        });
    }

    /**
     * Show SweetAlert confirmation dialog
     */
    function showConfirmation(element, onConfirm) {
        const title = element.dataset.confirmTitle || 'Are you sure?';
        const text = element.dataset.confirmText || 'You are about to perform an action.';
        const icon = element.dataset.confirmIcon || 'warning';
        const confirmText = element.dataset.confirmButtonText || 'Yes, proceed!';
        const cancelText = element.dataset.cancelButtonText || 'No, cancel';
        const confirmColor = element.dataset.confirmColor || '#28a745';
        const cancelColor = element.dataset.cancelColor || '#dc3545';

        Swal.fire({
            title: title,
            text: text,
            icon: icon,
            showCancelButton: true,
            confirmButtonColor: confirmColor,
            cancelButtonColor: cancelColor,
            confirmButtonText: confirmText,
            cancelButtonText: cancelText,
            width: '600px',
            customClass: {
                popup: 'swal2-popup-admin',
                confirmButton: 'swal2-confirm-admin',
                cancelButton: 'swal2-cancel-admin'
            }
        }).then((result) => {
            if (result.isConfirmed) {
                onConfirm();
            }
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initConfirmHandlers);
    } else {
        initConfirmHandlers();
    }

    // Also re-initialize after dynamic content loads (for AJAX-loaded content)
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length > 0) {
                initConfirmHandlers();
            }
        });
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
})();
