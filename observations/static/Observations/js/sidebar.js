/**
 * SIDEBAR NAVIGATION SYSTEM
 * Gère le comportement de la sidebar collapsible
 */

(function() {
    'use strict';

    // Clé pour localStorage
    const STORAGE_KEY = 'sidebarCollapsed';

    // Éléments DOM
    let sidebar = null;
    let content = null;
    let toggleBtn = null;
    let overlay = null;

    /**
     * Initialisation au chargement du DOM
     */
    document.addEventListener('DOMContentLoaded', function() {
        // Récupération des éléments
        sidebar = document.getElementById('sidebar');
        content = document.getElementById('content');
        toggleBtn = document.querySelector('.sidebar-toggle');
        overlay = document.querySelector('.sidebar-overlay');

        if (!sidebar || !content || !toggleBtn) {
            console.warn('Sidebar elements not found');
            return;
        }

        // Restaurer l'état de la sidebar depuis localStorage
        restoreSidebarState();

        // Attacher les événements
        attachEventListeners();

        // Mettre à jour le lien actif
        updateActiveLink();

        // Gestion responsive
        handleResize();
        window.addEventListener('resize', handleResize);
    });

    /**
     * Attache les écouteurs d'événements
     */
    function attachEventListeners() {
        // Toggle sidebar
        toggleBtn.addEventListener('click', toggleSidebar);

        // Fermeture par overlay (mobile)
        if (overlay) {
            overlay.addEventListener('click', closeSidebarMobile);
        }

        // Fermeture par touche Escape
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && window.innerWidth <= 768) {
                closeSidebarMobile();
            }
        });

        // Gestion du clic sur les liens
        const navLinks = sidebar.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                // Sur mobile, fermer la sidebar après clic
                if (window.innerWidth <= 768) {
                    closeSidebarMobile();
                }
            });
        });
    }

    /**
     * Toggle l'état de la sidebar
     */
    function toggleSidebar() {
        const isMobile = window.innerWidth <= 768;

        if (isMobile) {
            // Comportement mobile : show/hide
            sidebar.classList.toggle('active');
            if (overlay) {
                overlay.classList.toggle('active');
            }
        } else {
            // Comportement desktop : collapse/expand
            sidebar.classList.toggle('collapsed');
            content.classList.toggle('expanded');

            // Sauvegarder l'état
            saveSidebarState();
        }
    }

    /**
     * Ferme la sidebar en mode mobile
     */
    function closeSidebarMobile() {
        sidebar.classList.remove('active');
        if (overlay) {
            overlay.classList.remove('active');
        }
    }

    /**
     * Sauvegarde l'état de la sidebar
     */
    function saveSidebarState() {
        const isCollapsed = sidebar.classList.contains('collapsed');
        try {
            localStorage.setItem(STORAGE_KEY, isCollapsed ? 'true' : 'false');
        } catch (e) {
            console.warn('localStorage not available:', e);
        }
    }

    /**
     * Restaure l'état de la sidebar depuis localStorage
     */
    function restoreSidebarState() {
        // Ne pas appliquer sur mobile
        if (window.innerWidth <= 768) {
            return;
        }

        try {
            const isCollapsed = localStorage.getItem(STORAGE_KEY) === 'true';
            if (isCollapsed) {
                sidebar.classList.add('collapsed');
                content.classList.add('expanded');
            }
        } catch (e) {
            console.warn('localStorage not available:', e);
        }
    }

    /**
     * Met à jour le lien actif dans la sidebar
     */
    function updateActiveLink() {
        const currentPath = window.location.pathname;
        const navLinks = sidebar.querySelectorAll('.nav-link');

        navLinks.forEach(link => {
            // Retirer la classe active de tous les liens
            link.classList.remove('active');

            // Ajouter la classe active au lien correspondant
            const linkPath = new URL(link.href).pathname;
            if (currentPath === linkPath ||
                (linkPath !== '/' && currentPath.startsWith(linkPath))) {
                link.classList.add('active');
            }
        });

        // Cas spécial pour la page d'accueil
        if (currentPath === '/' || currentPath === '') {
            const homeLink = sidebar.querySelector('.nav-link[href="/"]');
            if (homeLink) {
                homeLink.classList.add('active');
            }
        }
    }

    /**
     * Gestion du comportement responsive
     */
    function handleResize() {
        const isMobile = window.innerWidth <= 768;

        if (isMobile) {
            // Retirer les classes desktop
            sidebar.classList.remove('collapsed');
            content.classList.remove('expanded');

            // S'assurer que la sidebar est cachée par défaut
            sidebar.classList.remove('active');
            if (overlay) {
                overlay.classList.remove('active');
            }
        } else {
            // Retirer les classes mobile
            sidebar.classList.remove('active');
            if (overlay) {
                overlay.classList.remove('active');
            }

            // Restaurer l'état desktop
            restoreSidebarState();
        }
    }

    /**
     * API publique (optionnelle)
     */
    window.SidebarAPI = {
        toggle: toggleSidebar,
        collapse: function() {
            if (window.innerWidth > 768) {
                sidebar.classList.add('collapsed');
                content.classList.add('expanded');
                saveSidebarState();
            }
        },
        expand: function() {
            if (window.innerWidth > 768) {
                sidebar.classList.remove('collapsed');
                content.classList.remove('expanded');
                saveSidebarState();
            }
        },
        isCollapsed: function() {
            return sidebar.classList.contains('collapsed');
        }
    };

})();
