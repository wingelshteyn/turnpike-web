/**
 * Scripts for the web application
 */

document.addEventListener('DOMContentLoaded', function () {

    // ===== Action Menus (three-dot dropdown) =====
    // Делегирование событий — надёжнее, чем привязка к кнопкам при загрузке.
    function closeAllActionMenus(exceptMenu) {
        document.querySelectorAll('.action-menu.open').forEach(function (m) {
            if (!exceptMenu || m !== exceptMenu) m.classList.remove('open');
        });
    }

    function positionMenu(btn, menuContent) {
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

    document.addEventListener('click', function (e) {
        var btn = e.target && e.target.closest ? e.target.closest('.action-menu .btn-menu') : null;
        if (btn) {
            e.stopPropagation();
            e.preventDefault();
            var menu = btn.closest('.action-menu');
            var menuContent = menu ? menu.querySelector('.menu-content') : null;
            closeAllActionMenus(menu);
            if (menu) menu.classList.toggle('open');
            if (menu && menu.classList.contains('open') && menuContent) {
                positionMenu(btn, menuContent);
            }
            return;
        }

        // Клик по самому меню — не закрываем
        var insideMenu = e.target && e.target.closest ? e.target.closest('.menu-content') : null;
        if (insideMenu) return;

        closeAllActionMenus(null);
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
