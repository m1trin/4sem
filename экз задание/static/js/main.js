// Client-side interactions for AIS Electronic Library

document.addEventListener('DOMContentLoaded', function() {
    // Initialize EasyMDE on description and review fields
    var mdEditors = document.querySelectorAll('.easymde-editor');
    mdEditors.forEach(function(textarea) {
        new EasyMDE({
            element: textarea,
            spellChecker: false,
            status: false,
            placeholder: "Напишите текст в формате Markdown...",
            minHeight: "200px"
        });
    });

    // Auto-close alert notifications after 5 seconds
    var alerts = document.querySelectorAll('.custom-alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});

// Confirmation function for book deletion
function confirmBookDeletion(event, title) {
    var confirmed = confirm("Вы уверены, что хотите удалить книгу " + title + "?");
    if (!confirmed) {
        event.preventDefault();
        return false;
    }
    return true;
}
