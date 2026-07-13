/*
========================================================================
   MaCave - Système de Gestion de Cave
   JavaScript Helper File
========================================================================
*/

document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Initialisation des icônes Lucide si disponibles
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // 2. Menu responsive pour Mobile
    const menuToggleBtn = document.querySelector('.menu-toggle');
    const sidebar = document.querySelector('.sidebar');

    if (menuToggleBtn && sidebar) {
        menuToggleBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            sidebar.classList.toggle('open');
        });

        // Fermer la barre latérale en cliquant à l'extérieur
        document.addEventListener('click', function(e) {
            if (!sidebar.contains(e.target) && !menuToggleBtn.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        });
    }

    // 3. Raccourci Ctrl + K pour focus sur la recherche
    const searchInput = document.querySelector('.search-box input');
    if (searchInput) {
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                searchInput.focus();
            }
        });
    }

    // 4. Gestion des Toasts (Alertes Django)
    const toasts = document.querySelectorAll('.alert-toast');
    toasts.forEach(toast => {
        // Bouton de fermeture manuelle
        const closeBtn = toast.querySelector('.alert-toast-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                dismissToast(toast);
            });
        }

        // Fermeture automatique après 5 secondes
        setTimeout(() => {
            dismissToast(toast);
        }, 5000);
    });

    function dismissToast(toast) {
        toast.style.opacity = '0';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }

    // 5. Dropdown Profil Utilisateur
    const userProfileBtn = document.querySelector('.user-profile-btn');
    const dropdownMenu = document.querySelector('.user-dropdown-menu');

    if (userProfileBtn && dropdownMenu) {
        userProfileBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdownMenu.classList.toggle('show');
        });

        document.addEventListener('click', function(e) {
            if (!userProfileBtn.contains(e.target) && !dropdownMenu.contains(e.target)) {
                dropdownMenu.classList.remove('show');
            }
        });
    }

    // 6. Loader Dynamique de Transition de Page
    const loader = document.getElementById('page-loader');

    // Cacher le loader au cas où il s'affiche par accident
    if (loader) {
        loader.classList.remove('visible');
    }

    // Intercepter le clic sur les liens pour afficher le loader
    document.addEventListener('click', function(e) {
        const link = e.target.closest('a');
        if (link) {
            const href = link.getAttribute('href');
            const target = link.getAttribute('target');

            // Filtrer pour n'afficher le loader que sur des transitions de page valides dans l'app
            if (href &&
                !href.startsWith('#') &&
                !href.startsWith('javascript:') &&
                !href.startsWith('mailto:') &&
                !href.startsWith('tel:') &&
                target !== '_blank' &&
                !e.ctrlKey &&
                !e.metaKey) {
                
                if (loader) {
                    loader.classList.add('visible');
                }
            }
        }
    });

    // Intercepter la soumission de formulaires
    document.addEventListener('submit', function(e) {
        const form = e.target;
        // On n'affiche pas de loader pour les formulaires ciblés vers un nouvel onglet
        if (form && form.getAttribute('target') !== '_blank') {
            if (loader) {
                loader.classList.add('visible');
            }
        }
    });
});
