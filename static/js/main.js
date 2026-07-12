// Facebook Clone - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const closeBtn = alert.querySelector('.btn-close');
            if (closeBtn) {
                closeBtn.click();
            }
        }, 5000);
    });

    // Character counter for post textarea
    const postTextarea = document.querySelector('textarea[name="content"]');
    if (postTextarea) {
        const maxLength = 5000;
        postTextarea.addEventListener('input', function() {
            if (this.value.length > maxLength) {
                this.value = this.value.substring(0, maxLength);
            }
        });
    }

    // AJAX like/unlike toggle (shared by post_card include on all pages)
    document.querySelectorAll('.like-form').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const btn = this.querySelector('button');
            const csrfToken = this.querySelector('[name=csrfmiddlewaretoken]').value;
            fetch(this.action, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.liked) {
                    btn.classList.remove('btn-outline-secondary');
                    btn.classList.add('btn-primary');
                    btn.innerHTML = '<i class="bi bi-hand-thumbs-up-fill"></i> Like';
                } else {
                    btn.classList.remove('btn-primary');
                    btn.classList.add('btn-outline-secondary');
                    btn.innerHTML = '<i class="bi bi-hand-thumbs-up"></i> Like';
                }
            })
            .catch(function() {
                // Silently fail — the page will show the result on next load
            });
        });
    });
});
