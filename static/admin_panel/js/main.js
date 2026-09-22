/* ══════════════════════════════════════════════════════════════
   AM Business Admin Panel – JavaScript
   ══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function() {

    // ─── Sidebar Toggle ───
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
        });
    }

    if (sidebarCloseBtn) {
        sidebarCloseBtn.addEventListener('click', function() {
            sidebar.classList.remove('open');
        });
    }

    // Close sidebar on click outside
    document.addEventListener('click', function(e) {
        if (sidebar && sidebar.classList.contains('open') &&
            !sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
            sidebar.classList.remove('open');
        }
    });

    // ─── Dropdowns ───
    document.querySelectorAll('.dropdown-toggle').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const menu = this.nextElementSibling;
            // Close all other dropdowns
            document.querySelectorAll('.dropdown-menu.show').forEach(function(m) {
                if (m !== menu) m.classList.remove('show');
            });
            menu.classList.toggle('show');
        });
    });

    document.addEventListener('click', function() {
        document.querySelectorAll('.dropdown-menu.show').forEach(function(m) {
            m.classList.remove('show');
        });
    });

    // ─── Tabs ───
    document.querySelectorAll('.tab-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const group = this.closest('.tabs').dataset.group || 'default';
            const target = this.dataset.tab;

            // Update active tab button
            this.closest('.tabs').querySelectorAll('.tab-btn').forEach(function(b) {
                b.classList.remove('active');
            });
            this.classList.add('active');

            // Show target content
            document.querySelectorAll('.tab-content[data-group="' + group + '"]').forEach(function(c) {
                c.classList.remove('active');
            });
            var targetEl = document.getElementById(target);
            if (targetEl) targetEl.classList.add('active');
        });
    });

    // ─── Modal ───
    const modalOverlay = document.getElementById('modalOverlay');
    const modal = document.getElementById('modal');
    const modalClose = document.getElementById('modalClose');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');

    window.openModal = function(title, bodyHTML) {
        if (modalTitle) modalTitle.textContent = title;
        if (modalBody) modalBody.innerHTML = bodyHTML;
        if (modalOverlay) modalOverlay.classList.add('show');
    };

    window.closeModal = function() {
        if (modalOverlay) modalOverlay.classList.remove('show');
    };

    if (modalClose) {
        modalClose.addEventListener('click', closeModal);
    }

    if (modalOverlay) {
        modalOverlay.addEventListener('click', function(e) {
            if (e.target === modalOverlay) closeModal();
        });
    }

    // ─── Delete Confirmation ───
    window.confirmDelete = function(formId) {
        if (confirm(window.DSH_I18N && window.DSH_I18N.confirmDelete || 'Are you sure you want to delete this item?')) {
            document.getElementById(formId).submit();
        }
    };

    // ─── Bulk Actions ───
    // Each admin list page renders a `.bulk-form` holding the hidden
    // `action`/`bulk_action` inputs and the toolbar. The row checkboxes live
    // inside the table (so they can sit in their own cells) and are linked to
    // the form through the HTML5 `form="<id>"` attribute — which means they
    // must be looked up on the document, not inside the form element.
    document.querySelectorAll('.bulk-form').forEach(function(form) {
        var formId = form.id;
        var rowChecks = Array.prototype.slice.call(
            document.querySelectorAll('input.row-check[form="' + formId + '"]')
        );
        var selectAll = document.querySelector('input.select-all[form="' + formId + '"]');
        var actionSelect = form.querySelector('.bulk-select');
        var actionInput = form.querySelector('.bulk-action-input');
        var applyBtn = form.querySelector('.bulk-apply');
        var clearBtn = form.querySelector('.bulk-clear');
        var bar = form.querySelector('.bulk-bar');
        var countEl = form.querySelector('.bulk-count-value');
        var i18n = window.DSH_I18N || {};

        if (!rowChecks.length) return;

        function selectedRows() {
            return rowChecks.filter(function(c) { return c.checked; });
        }

        function sync() {
            var chosen = selectedRows();
            var n = chosen.length;

            if (countEl) countEl.textContent = n;
            if (bar) bar.classList.toggle('active', n > 0);
            if (selectAll) {
                selectAll.checked = n > 0 && n === rowChecks.length;
                selectAll.indeterminate = n > 0 && n < rowChecks.length;
            }

            rowChecks.forEach(function(c) {
                var tr = c.closest('tr');
                if (tr) tr.classList.toggle('row-selected', c.checked);
            });
        }

        function setAll(state) {
            rowChecks.forEach(function(c) { c.checked = state; });
            sync();
        }

        if (selectAll) {
            selectAll.addEventListener('change', function() { setAll(selectAll.checked); });
        }

        rowChecks.forEach(function(c) {
            c.addEventListener('change', sync);
        });

        if (clearBtn) {
            clearBtn.addEventListener('click', function(e) {
                e.preventDefault();
                setAll(false);
                if (actionSelect) actionSelect.selectedIndex = 0;
            });
        }

        if (applyBtn) {
            applyBtn.addEventListener('click', function(e) {
                var chosen = selectedRows();
                if (!chosen.length) {
                    e.preventDefault();
                    alert(i18n.bulkNoSelection || 'Select at least one row first.');
                    return;
                }
                if (!actionSelect || !actionSelect.value) {
                    e.preventDefault();
                    alert(i18n.bulkNoAction || 'Choose a bulk action first.');
                    if (actionSelect) actionSelect.focus();
                    return;
                }
                var option = actionSelect.options[actionSelect.selectedIndex];
                if (option && option.dataset.confirm === '1') {
                    var template = i18n.bulkConfirmDelete ||
                        'Delete %s selected item(s)? This cannot be undone.';
                    if (!confirm(template.replace('%s', chosen.length))) {
                        e.preventDefault();
                        return;
                    }
                }
                if (actionInput) actionInput.value = actionSelect.value;
            });
        }

        // Reflect checkboxes restored by the browser (back/forward navigation)
        sync();
    });

    // ─── Form submission to modal ───
    window.openEditModal = function(title, formHTML) {
        openModal(title, formHTML);
    };

    // ─── Mobile: close sidebar on nav click ───
    document.querySelectorAll('.sidebar-nav .nav-item').forEach(function(item) {
        item.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                sidebar.classList.remove('open');
            }
        });
    });

    // ─── Image Preview Before Upload (global, works with modal-injected forms) ───
    // Uses event delegation on document so it catches file inputs in modals too.
    document.addEventListener('change', function(e) {
        var input = e.target;
        if (input.tagName === 'INPUT' && input.type === 'file') {
            // Find or create preview container right after the input
            var parent = input.parentElement;
            var previewId = 'preview-' + input.name;
            var existing = document.getElementById(previewId);

            if (!input.files || !input.files[0]) {
                if (existing) existing.style.display = 'none';
                return;
            }

            var file = input.files[0];
            if (!file.type.startsWith('image/')) {
                if (existing) existing.style.display = 'none';
                return;
            }

            if (!existing) {
                existing = document.createElement('div');
                existing.id = previewId;
                existing.style.cssText = 'margin-top:8px;margin-bottom:8px;';
                var img = document.createElement('img');
                img.style.cssText = 'max-width:200px;max-height:150px;border-radius:8px;border:2px solid var(--border-color,#ddd);object-fit:contain;';
                existing.appendChild(img);
                // Insert right after the input
                input.parentNode.insertBefore(existing, input.nextSibling);
            }

            var previewImg = existing.querySelector('img');
            previewImg.src = URL.createObjectURL(file);
            existing.style.display = 'block';

            // Revoke object URL after load to free memory
            previewImg.onload = function() {
                URL.revokeObjectURL(this.src);
            };
        }
    });

    // Also re-scan for file inputs when modal opens (in case change delegation misses)
    var originalOpenModal = window.openModal;
    if (originalOpenModal) {
        window.openModal = function(title, bodyHTML) {
            originalOpenModal(title, bodyHTML);
            // The change event delegation will handle file inputs in the modal
        };
    }

});
