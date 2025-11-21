/**
 * Script pour forcer le menu de navigation latéral à être replié par défaut
 * et gérer le pliage/dépliage de la table des matières
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Navigation script loaded');

    // ===== NAVIGATION LATÉRALE (GAUCHE) =====

    // Fonction pour replier tous les menus sauf le chemin actif
    function collapseInactiveMenus() {
        // Sélectionner tous les items de navigation principale (gauche) avec des sous-menus
        const navItems = document.querySelectorAll('.md-nav--primary .md-nav__item--nested');

        navItems.forEach(item => {
            // Si l'item n'est pas actif ou dans le chemin actif
            if (!item.classList.contains('md-nav__item--active')) {
                // Trouver le checkbox de toggle
                const toggle = item.querySelector(':scope > .md-nav__toggle');
                if (toggle && toggle.checked) {
                    toggle.checked = false;
                }
            }
        });
    }

    // ===== TABLE DES MATIÈRES (DROITE) =====

    // Variable globale pour stocker les items TOC
    let tocCollapsibleItems = [];

    // Fonction pour fermer tous les items TOC sauf un
    function closeAllTOCExcept(exceptItem) {
        tocCollapsibleItems.forEach(item => {
            if (item !== exceptItem && !item.classList.contains('toc-collapsed')) {
                const subNav = item.querySelector(':scope > .md-nav');
                const arrow = item.querySelector('.toc-arrow');

                if (subNav) {
                    subNav.style.display = 'none';
                    item.classList.add('toc-collapsed');
                    if (arrow) {
                        arrow.style.transform = 'rotate(0deg)';
                    }
                }
            }
        });
    }

    // Fonction pour ouvrir un item TOC spécifique
    function openTOCItem(item) {
        if (!item || !item.classList.contains('toc-collapsible')) return;

        const subNav = item.querySelector(':scope > .md-nav');
        const arrow = item.querySelector('.toc-arrow');

        if (subNav) {
            subNav.style.display = 'block';
            item.classList.remove('toc-collapsed');
            if (arrow) {
                arrow.style.transform = 'rotate(90deg)';
            }
        }
    }

    // Fonction pour initialiser le système de pliage de la TOC
    function initTOCCollapse() {
        console.log('Initializing TOC collapse system...');

        const sidebar = document.querySelector('.md-sidebar--secondary');
        if (!sidebar) {
            console.log('No TOC sidebar found');
            return;
        }

        // Trouver tous les items de niveau 2 (H2) qui ont des sous-items (H3+)
        const tocList = sidebar.querySelector('.md-nav__list');
        if (!tocList) {
            console.log('No TOC list found');
            return;
        }

        // Réinitialiser le tableau
        tocCollapsibleItems = [];
        let processedCount = 0;

        // Parcourir tous les items de premier niveau (H2)
        const level1Items = tocList.querySelectorAll(':scope > .md-nav__item');

        level1Items.forEach((item, index) => {
            // Chercher s'il a des sous-items
            const subNav = item.querySelector(':scope > .md-nav');

            if (subNav && subNav.children.length > 0) {
                // Cet item a des sous-items (H3+), le rendre pliable
                console.log(`Found H2 with sub-items: ${item.textContent.substring(0, 30)}...`);

                // Marquer l'item comme pliable
                item.classList.add('toc-collapsible');
                tocCollapsibleItems.push(item);

                // Cacher les sous-items par défaut
                subNav.style.display = 'none';
                item.classList.add('toc-collapsed');

                // Trouver le lien principal
                const link = item.querySelector(':scope > .md-nav__link');
                if (link) {
                    // Nettoyer les flèches existantes (si réinitialisation)
                    const existingArrow = link.querySelector('.toc-arrow');
                    if (existingArrow) {
                        existingArrow.remove();
                    }

                    // Ajouter une flèche
                    const arrow = document.createElement('span');
                    arrow.className = 'toc-arrow';
                    arrow.textContent = '▶ ';
                    arrow.style.marginRight = '4px';
                    arrow.style.fontSize = '0.7em';
                    arrow.style.display = 'inline-block';
                    arrow.style.transition = 'transform 0.3s ease';
                    link.insertBefore(arrow, link.firstChild);

                    // Rendre le lien cliquable pour toggle
                    link.style.cursor = 'pointer';

                    // Ajouter l'événement de clic (COMPORTEMENT ACCORDÉON)
                    link.addEventListener('click', function(e) {
                        // Ne pas suivre le lien, juste toggle
                        e.preventDefault();

                        const isCollapsed = item.classList.contains('toc-collapsed');

                        if (isCollapsed) {
                            // Fermer tous les autres items (accordéon)
                            closeAllTOCExcept(item);

                            // Déplier cet item
                            openTOCItem(item);
                        } else {
                            // Replier
                            subNav.style.display = 'none';
                            item.classList.add('toc-collapsed');
                            arrow.style.transform = 'rotate(0deg)';
                        }
                    });
                }

                processedCount++;
            }
        });

        console.log(`Processed ${processedCount} collapsible TOC items`);
    }

    // Fonction pour déplier la section active dans la TOC (avec comportement accordéon)
    function expandActiveTOCSection() {
        const sidebar = document.querySelector('.md-sidebar--secondary');
        if (!sidebar) return;

        // Trouver l'item actif
        const activeItem = sidebar.querySelector('.md-nav__item--active');
        if (!activeItem) return;

        // Remonter pour trouver le parent de niveau 1 (H2)
        let parentH2 = activeItem;
        while (parentH2 && !parentH2.parentElement?.classList.contains('md-nav__list')) {
            parentH2 = parentH2.parentElement?.closest('.md-nav__item');
        }

        if (parentH2 && parentH2.classList.contains('toc-collapsible')) {
            // Fermer tous les autres items (accordéon)
            closeAllTOCExcept(parentH2);

            // Ouvrir uniquement cet item
            openTOCItem(parentH2);
        }
    }

    // ===== SYNCHRONISATION AVEC LE SCROLL =====

    let scrollTimeout;
    let lastActiveSection = null;

    // Fonction pour trouver l'élément qui scroll réellement
    function findScrollingElement() {
        // Material for MkDocs peut utiliser différents conteneurs pour le scroll
        const candidates = [
            document.querySelector('.md-main'),
            document.querySelector('.md-content'),
            document.querySelector('[data-md-component="container"]'),
            document.documentElement,
            document.body,
            window
        ];

        console.log('Searching for scrolling element...');
        for (const el of candidates) {
            if (!el) continue;

            const isWindow = el === window;
            const scrollHeight = isWindow ? document.documentElement.scrollHeight : el.scrollHeight;
            const clientHeight = isWindow ? window.innerHeight : el.clientHeight;
            const scrollTop = isWindow ? window.scrollY : el.scrollTop;

            console.log(`Checking ${isWindow ? 'window' : el.className}:`, {
                scrollHeight,
                clientHeight,
                scrollTop,
                canScroll: scrollHeight > clientHeight
            });

            if (scrollHeight > clientHeight) {
                console.log(`Found scrolling element: ${isWindow ? 'window' : el.className}`);
                return el;
            }
        }

        console.log('No scrolling element found, defaulting to window');
        return window;
    }

    // Fonction pour trouver la section actuellement visible
    function findCurrentSection() {
        // Essayer différents sélecteurs pour être plus robuste
        const headings = document.querySelectorAll('h2[id], h3[id], .md-content h2[id], .md-content h3[id]');

        // Trouver l'élément qui scroll pour obtenir la bonne position
        const scrollingEl = findScrollingElement();
        const isWindow = scrollingEl === window;
        const scrollPosition = (isWindow ? window.scrollY : scrollingEl.scrollTop) + 150;

        let currentSection = null;

        headings.forEach(heading => {
            const headingTop = heading.getBoundingClientRect().top + (isWindow ? window.scrollY : scrollingEl.scrollTop);
            if (headingTop <= scrollPosition) {
                currentSection = heading;
            }
        });

        return currentSection;
    }

    // Fonction pour synchroniser la TOC avec le scroll
    function syncTOCWithScroll() {
        const currentSection = findCurrentSection();

        if (!currentSection) {
            console.log('No current section found');
            return;
        }

        const currentId = currentSection.id;
        if (!currentId) {
            console.log('Current section has no ID');
            return;
        }

        // Éviter les mises à jour inutiles
        if (lastActiveSection === currentId) return;

        console.log(`Section changed: ${lastActiveSection} -> ${currentId}`);
        lastActiveSection = currentId;

        const sidebar = document.querySelector('.md-sidebar--secondary');
        if (!sidebar) {
            console.log('No sidebar found');
            return;
        }

        // Trouver l'item TOC correspondant
        const tocLink = sidebar.querySelector(`a[href="#${currentId}"]`);
        if (!tocLink) {
            console.log(`No TOC link found for #${currentId}`);
            return;
        }

        console.log(`Found TOC link for #${currentId}`);

        // Trouver le parent H2
        const tocItem = tocLink.closest('.md-nav__item');
        if (!tocItem) {
            console.log('No TOC item found');
            return;
        }

        // Trouver le H2 parent si on est sur un H3
        let parentH2Item = tocItem;

        // Vérifier si c'est un sous-item (H3) - chercher le parent .md-nav
        const parentNav = tocItem.parentElement;
        if (parentNav && parentNav.classList.contains('md-nav')) {
            // C'est potentiellement un H3, chercher le .md-nav__item parent
            const potentialH2 = parentNav.closest('.md-nav__item');
            if (potentialH2 && potentialH2.classList.contains('toc-collapsible')) {
                parentH2Item = potentialH2;
                console.log('Found parent H2 for H3');
            }
        }

        console.log(`Parent H2 item:`, parentH2Item);

        // Si on a trouvé un H2 pliable, l'ouvrir (avec comportement accordéon)
        if (parentH2Item && parentH2Item.classList.contains('toc-collapsible')) {
            console.log('Opening TOC item (with accordion behavior)');
            // Fermer tous les autres
            closeAllTOCExcept(parentH2Item);
            // Ouvrir celui-ci
            openTOCItem(parentH2Item);
        } else {
            console.log('Parent H2 item is not collapsible or not found');
        }
    }

    // Gestionnaire d'événement de scroll avec debouncing
    function handleScroll(event) {
        const scrollingEl = findScrollingElement();
        const isWindow = scrollingEl === window;
        const scrollY = isWindow ? window.scrollY : scrollingEl.scrollTop;

        console.log('Scroll event detected!', {
            target: event?.target?.className || event?.target?.nodeName || 'window',
            scrollY: scrollY,
            isWindow: isWindow
        });

        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
            console.log('Running syncTOCWithScroll after debounce');
            syncTOCWithScroll();
        }, 100);
    }

    // Variable pour stocker les listeners actifs
    let activeScrollListeners = [];

    // Fonction pour attacher les listeners de scroll
    function attachScrollListeners() {
        // Retirer les anciens listeners d'abord
        activeScrollListeners.forEach(({element, handler}) => {
            element.removeEventListener('scroll', handler);
        });
        activeScrollListeners = [];

        console.log('Attaching scroll listeners...');

        // Trouver l'élément qui scroll
        const scrollingEl = findScrollingElement();
        const isWindow = scrollingEl === window;
        const isDocElement = scrollingEl === document.documentElement || scrollingEl === document.body;

        // IMPORTANT: Si c'est document.documentElement ou document.body qui scroll,
        // les événements sont déclenchés sur window, pas sur l'élément lui-même
        const eventTarget = (isWindow || isDocElement) ? window : scrollingEl;

        console.log('Scroll detection:', {
            scrollingElement: isWindow ? 'window' : scrollingEl.className,
            isDocElement: isDocElement,
            eventTarget: eventTarget === window ? 'window' : eventTarget.className
        });

        // Attacher le listener sur la bonne cible
        eventTarget.addEventListener('scroll', handleScroll, { passive: true });
        activeScrollListeners.push({element: eventTarget, handler: handleScroll});

        console.log(`Scroll listener attached to: ${eventTarget === window ? 'window' : eventTarget.className}`);

        // Test: déclencher manuellement pour voir si ça marche
        setTimeout(() => {
            console.log('Testing scroll listener...');
            const scrollY = isWindow ? window.scrollY : scrollingEl.scrollTop;
            console.log('Current scroll position:', scrollY);
            console.log('Scrollable height:', isWindow ? document.documentElement.scrollHeight : scrollingEl.scrollHeight);
            console.log('Try scrolling the page now!');
        }, 500);
    }

    // ===== INITIALISATION =====

    // Fonction d'initialisation complète
    function initializeAll() {
        console.log('Running full initialization...');
        collapseInactiveMenus();
        initTOCCollapse();
        expandActiveTOCSection();
        attachScrollListeners();
        // Réinitialiser le tracking
        lastActiveSection = null;
        console.log('Initialization complete');
    }

    // Appliquer au chargement initial
    collapseInactiveMenus();
    setTimeout(() => {
        initializeAll();
    }, 100);

    // Réappliquer après chaque navigation (pour les SPAs avec navigation.instant)
    if (typeof app !== 'undefined' && app.document$) {
        console.log('Material instant navigation detected - subscribing to document changes');
        app.document$.subscribe(() => {
            console.log('Page changed via instant navigation - reinitializing...');
            setTimeout(initializeAll, 200);
        });
    }

    // Ajouter un gestionnaire de clic sur les liens de navigation
    document.addEventListener('click', function(e) {
        // Si c'est un lien de navigation principale
        if (e.target.closest('.md-nav--primary .md-nav__link')) {
            console.log('Navigation link clicked - will reinitialize');
            setTimeout(initializeAll, 400);
        }
    });

    console.log('Navigation and TOC system fully initialized');
});
