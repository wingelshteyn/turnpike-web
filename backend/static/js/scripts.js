/**
 * Scripts for the web application
 */

document.addEventListener('DOMContentLoaded', function () {

    // ===== Action Menus (three-dot dropdown) =====
    // Делегирование событий — надёжнее, чем привязка к кнопкам при загрузке.
    var openState = null; // { menu, btn, menuContent }

    function detachMenuContent(menu, menuContent) {
        if (!menuContent) return;
        if (menuContent.__tpDetached) return;
        // placeholder чтобы вернуть обратно в DOM
        var ph = document.createElement('span');
        ph.style.display = 'none';
        ph.__tpFor = menuContent;
        menuContent.__tpPlaceholder = ph;
        menuContent.__tpParent = menuContent.parentNode;
        menuContent.__tpNext = menuContent.nextSibling;
        if (menuContent.parentNode) menuContent.parentNode.insertBefore(ph, menuContent);
        document.body.appendChild(menuContent);
        menuContent.__tpDetached = true;
        // фиксируем позиционирование относительно viewport
        menuContent.style.position = 'fixed';
        menuContent.style.zIndex = '10000';
    }

    function attachMenuContent(menuContent) {
        if (!menuContent || !menuContent.__tpDetached) return;
        try {
            var ph = menuContent.__tpPlaceholder;
            if (ph && ph.parentNode) {
                ph.parentNode.insertBefore(menuContent, ph);
                ph.parentNode.removeChild(ph);
            } else if (menuContent.__tpParent) {
                // fallback
                menuContent.__tpParent.appendChild(menuContent);
            }
        } catch (e) {
            // ignore
        }
        menuContent.__tpDetached = false;
        menuContent.__tpPlaceholder = null;
        menuContent.__tpParent = null;
        menuContent.__tpNext = null;
        menuContent.style.position = '';
        menuContent.style.display = '';
    }

    function closeAllActionMenus(exceptMenu) {
        document.querySelectorAll('.action-menu.open').forEach(function (m) {
            if (exceptMenu && m === exceptMenu) return;
            m.classList.remove('open');
            var c = m.querySelector('.menu-content');
            if (c) c.style.display = 'none';
            attachMenuContent(c);
        });
        if (!exceptMenu) openState = null;
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

    function repositionOpenMenu() {
        if (!openState) return;
        if (!openState.menu || !openState.menu.classList.contains('open')) return;
        if (!openState.btn || !openState.menuContent) return;
        positionMenu(openState.btn, openState.menuContent);
    }

    window.addEventListener('scroll', repositionOpenMenu, true);
    window.addEventListener('resize', repositionOpenMenu);

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
                detachMenuContent(menu, menuContent);
                menuContent.style.display = 'block';
                openState = { menu: menu, btn: btn, menuContent: menuContent };
                positionMenu(btn, menuContent);
            } else if (menu && !menu.classList.contains('open') && menuContent) {
                menuContent.style.display = 'none';
                attachMenuContent(menuContent);
                openState = null;
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
