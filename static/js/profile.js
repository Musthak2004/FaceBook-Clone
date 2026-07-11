// Profile page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Image preview for profile picture & cover photo
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(ev) {
                    const preview = input.closest('form').querySelector('.image-preview');
                    if (preview) {
                        preview.src = ev.target.result;
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    });
});
