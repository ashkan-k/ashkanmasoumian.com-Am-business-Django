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

});
