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
        // запоминаем на меню, чтобы уметь закрывать даже когда content в body
        if (menu) menu.__tpDetachedContent = menuContent;
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

    function getMenuContentFor(menu) {
        if (!menu) return null;
        return menu.querySelector('.menu-content') || menu.__tpDetachedContent || null;
    }

    function closeAllActionMenus(exceptMenu) {
        document.querySelectorAll('.action-menu.open').forEach(function (m) {
            if (exceptMenu && m === exceptMenu) return;
            m.classList.remove('open');
            var c = getMenuContentFor(m);
            if (c) c.style.display = 'none';
            attachMenuContent(c);
            if (m.__tpDetachedContent === c) m.__tpDetachedContent = null;
        });
        // если было открыто меню и оно уже не в DOM-дереве .action-menu — закрываем по openState
        if (openState && openState.menu && (!exceptMenu || openState.menu !== exceptMenu)) {
            try {
                if (openState.menu) openState.menu.classList.remove('open');
                if (openState.menuContent) {
                    openState.menuContent.style.display = 'none';
                    attachMenuContent(openState.menuContent);
                }
                if (openState.menu) openState.menu.__tpDetachedContent = null;
            } catch (e) {}
        }
        if (!exceptMenu) openState = null;
    }

    function positionMenu(btn, menuContent) {
        var rect = btn.getBoundingClientRect();
        var margin = 8;
        var menuWidth = 180;
        // Позиционируем справа от кнопки "...", а если не влезает — слева.
        var preferredLeft = rect.right + margin;
        var fallbackLeft = rect.left - menuWidth - margin;
        var left = preferredLeft;
        if (preferredLeft + menuWidth > window.innerWidth - margin) {
            left = fallbackLeft;
        }
        left = Math.max(margin, Math.min(left, window.innerWidth - menuWidth - margin));

        menuContent.style.left = left + 'px';
        menuContent.style.right = 'auto';
        // по верхнему краю кнопки, чтобы меню выглядело «справа от ...»
        menuContent.style.top = Math.max(margin, rect.top) + 'px';
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

    // Надёжное закрытие по клику вне меню (capture-фаза)
    document.addEventListener('pointerdown', function (e) {
        if (!openState || !openState.menu || !openState.menuContent) return;
        var t = e.target;
        if (t && t.closest) {
            if (t.closest('.menu-content')) return;
            if (t.closest('.action-menu .btn-menu')) return;
        }
        closeAllActionMenus(null);
    }, true);

    document.addEventListener('click', function (e) {
        var btn = e.target && e.target.closest ? e.target.closest('.action-menu .btn-menu') : null;
        if (btn) {
            e.stopPropagation();
            e.preventDefault();
            var menu = btn.closest('.action-menu');
            var menuContent = menu ? getMenuContentFor(menu) : null;
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
                if (menu.__tpDetachedContent === menuContent) menu.__tpDetachedContent = null;
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
