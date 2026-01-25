/**
 * Gestion des observations (tableau dynamique)
 * Gère le marquage pour suppression/restauration des lignes d'observation,
 * la mise à jour de la bannière d'avertissement et la confirmation avant soumission.
 */
export default function initObservationRowsManager() {
    'use strict';

    let deletionCount = 0;
    const mainForm = document.querySelector('form[method="post"]:not([action*="logout"])');

    function updateDeleteBanner() {
        const banner = document.getElementById('delete-confirmation-banner');
        const countElement = document.getElementById('delete-count');
        if (!banner || !countElement) return;

        deletionCount = document.querySelectorAll('.observation-row.marked-for-deletion').length;
        countElement.textContent = deletionCount;

        if (deletionCount > 0) {
            banner.classList.add('show');
        } else {
            banner.classList.remove('show');
        }
    }

    function setupRow(row) {
        const deleteBtn = row.querySelector('.delete-observation-btn');
        const restoreBtn = row.querySelector('.restore-observation-btn');
        const deleteCheckbox = row.querySelector('input[type="checkbox"][name*="-DELETE"]');

        if (!deleteBtn || !restoreBtn || !deleteCheckbox) return;

        // Action for the delete button
        deleteBtn.addEventListener('click', function() {
            deleteCheckbox.checked = true;
            row.classList.add('marked-for-deletion');
            row.querySelectorAll('input, textarea').forEach(el => {
                if (el !== deleteCheckbox) el.disabled = true;
            });
            deleteBtn.style.display = 'none';
            restoreBtn.style.display = 'inline-block';
            updateDeleteBanner();
        });

        // Action for the restore button
        restoreBtn.addEventListener('click', function() {
            deleteCheckbox.checked = false;
            row.classList.remove('marked-for-deletion');
            row.querySelectorAll('input, textarea').forEach(el => {
                el.disabled = false;
            });
            deleteBtn.style.display = 'inline-block';
            restoreBtn.style.display = 'none';
            updateDeleteBanner();
        });
    }

    // Setup all existing rows
    document.querySelectorAll('.observation-row').forEach(setupRow);

    // Observer les nouvelles lignes ajoutées dynamiquement (si le DOM change)
    // Note: Cela pourrait être redondant avec l'observer de TimeManager, 
    // mais permet à ce module d'être autonome.
    const observationsTable = document.querySelector('.observations-table tbody');
    if (observationsTable) {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1 && node.classList.contains('observation-row')) {
                        setupRow(node);
                    }
                });
            });
        });

        observer.observe(observationsTable, {
            childList: true,
            subtree: true
        });
    }

    // Setup the "Clear all deletions" button
    const clearAllBtn = document.getElementById('clear-all-deletions');
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', function(e) {
            e.preventDefault();
            document.querySelectorAll('.observation-row.marked-for-deletion .restore-observation-btn').forEach(btn => {
                btn.click();
            });
        });
    }

    // Add confirmation before submitting the form
    if (mainForm) {
        mainForm.addEventListener('submit', function(e) {
            // Re-enable all disabled fields right before submission so their values are sent
            document.querySelectorAll('.observation-row.marked-for-deletion input, .observation-row.marked-for-deletion textarea').forEach(el => {
                el.disabled = false;
            });

            if (deletionCount > 0) {
                const message = `Voulez-vous vraiment supprimer ${deletionCount} observation${deletionCount > 1 ? 's' : ''} ?`;
                if (!confirm(message)) {
                    e.preventDefault();
                    // If submission is cancelled, re-disable the fields
                    document.querySelectorAll('.observation-row.marked-for-deletion input, .observation-row.marked-for-deletion textarea').forEach(el => {
                        const deleteCheckbox = el.closest('.observation-row').querySelector('input[type="checkbox"][name*="-DELETE"]');
                        if (el !== deleteCheckbox) {
                            el.disabled = true;
                        }
                    });
                    return false;
                }
            }
        });
    }
    
    console.log('Module Gestion Observations initialisé');
}
