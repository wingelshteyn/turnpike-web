/**
 * Scripts for the web application
 */

document.addEventListener('DOMContentLoaded', function () {

    // ===== Action Menus (three-dot dropdown) =====
    document.querySelectorAll('.action-menu .btn-menu').forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            e.stopPropagation();
            var menu = this.closest('.action-menu');
            var menuContent = menu.querySelector('.menu-content');
            // Close all other menus
            document.querySelectorAll('.action-menu.open').forEach(function (m) {
                if (m !== menu) m.classList.remove('open');
            });
            menu.classList.toggle('open');
            // Position menu with fixed - outside table, never clipped
            if (menu.classList.contains('open') && menuContent) {
                var rect = btn.getBoundingClientRect();
                var margin = 8;
                var menuWidth = 180;
                var left = Math.max(margin, Math.min(rect.right - menuWidth, window.innerWidth - menuWidth - margin));
                menuContent.style.left = left + 'px';
                menuContent.style.right = 'auto';
                menuContent.style.top = (rect.bottom + margin) + 'px';
                menuContent.style.bottom = 'auto';
                requestAnimationFrame(function () {
                    var menuRect = menuContent.getBoundingClientRect();
                    if (menuRect.bottom > window.innerHeight - margin) {
                        menuContent.style.top = 'auto';
                        menuContent.style.bottom = (window.innerHeight - rect.top + margin) + 'px';
                    }
                });
            }
        });
    });

    // Close menus on outside click
    document.addEventListener('click', function () {
        document.querySelectorAll('.action-menu.open').forEach(function (m) {
            m.classList.remove('open');
        });
    });

    // ===== Toggle Details Columns =====
    document.querySelectorAll('.toggle-details-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var table = this.closest('table');
            if (table) {
                table.classList.toggle('show-details');
                var showing = table.classList.contains('show-details');
                table.querySelectorAll('.toggle-details-btn').forEach(function (b) {
                    b.textContent = showing ? 'Скрыть подробности' : 'Показать подробности';
                });
            }
        });
    });

    // ===== Sidebar active link =====
    var currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar-content a').forEach(function (link) {
        var href = link.getAttribute('href');
        if (href === currentPath || (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('active');
        }
    });

});
