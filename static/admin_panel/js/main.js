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
        if (confirm('Are you sure you want to delete this item?')) {
            document.getElementById(formId).submit();
        }
    };

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
