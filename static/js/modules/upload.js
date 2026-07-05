/* ============================================================
   Upload module — Image preview, drag-and-drop
   ============================================================ */

export function initImagePreview() {
  document.querySelectorAll('input[type="file"][data-preview]').forEach(function (input) {
    var previewId = input.getAttribute('data-preview');
    var preview = document.getElementById(previewId);
    if (!preview) return;

    input.addEventListener('change', function () {
      var file = this.files[0];
      if (file) {
        var reader = new FileReader();
        reader.onload = function (e) {
          preview.src = e.target.result;
          preview.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
      }
    });
  });
}

export function initDragDrop() {
  document.querySelectorAll('.drop-zone').forEach(function (zone) {
    var input = zone.querySelector('input[type="file"]');
    if (!input) return;

    zone.addEventListener('dragover', function (e) {
      e.preventDefault();
      zone.classList.add('drag-over');
    });

    zone.addEventListener('dragleave', function () {
      zone.classList.remove('drag-over');
    });

    zone.addEventListener('drop', function (e) {
      e.preventDefault();
      zone.classList.remove('drag-over');

      if (e.dataTransfer.files.length) {
        input.files = e.dataTransfer.files;
        var event = new Event('change', { bubbles: true });
        input.dispatchEvent(event);
      }
    });
  });
}

export function initImageUploadButtons() {
  document.querySelectorAll('[data-upload-trigger]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var inputId = this.getAttribute('data-upload-trigger');
      var input = document.getElementById(inputId);
      if (input) input.click();
    });
  });

  document.querySelectorAll('.image-upload-area').forEach(function (area) {
    area.addEventListener('click', function () {
      var input = this.nextElementSibling;
      while (input && input.tagName !== 'INPUT') {
        input = input.nextElementSibling;
      }
      if (input) input.click();
    });
  });
}

export function initPostImageUpload() {
  var form = document.getElementById('create-post-form');
  if (!form) return;

  var imageInput = form.querySelector('input[name="images"]');
  var previewContainer = form.querySelector('.image-preview-container');

  if (!imageInput || !previewContainer) return;

  imageInput.addEventListener('change', function () {
    previewContainer.innerHTML = '';
    Array.from(this.files).forEach(function (file) {
      var reader = new FileReader();
      reader.onload = function (e) {
        var div = document.createElement('div');
        div.className = 'image-preview-item';
        div.innerHTML =
          '<img src="' + e.target.result + '" alt="Upload preview">' +
          '<button type="button" class="image-preview-remove">&times;</button>';
        previewContainer.appendChild(div);

        div.querySelector('.image-preview-remove').addEventListener('click', function () {
          div.remove();
        });
      };
      reader.readAsDataURL(file);
    });
  });
}

export function initProfileUpload() {
  var profileInput = document.getElementById('id_profile_picture');
  var coverInput = document.getElementById('id_cover_photo');

  if (profileInput) {
    profileInput.setAttribute('data-preview', 'profile-preview');
  }
  if (coverInput) {
    coverInput.setAttribute('data-preview', 'cover-preview');
  }
}

export function initUpload() {
  initImagePreview();
  initDragDrop();
  initImageUploadButtons();
  initPostImageUpload();
  initProfileUpload();
}
