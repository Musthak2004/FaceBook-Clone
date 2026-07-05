/* ============================================================
   Gallery — Lightbox for multi-image posts
   Uses event delegation so it works with infinite-scroll posts.
   ============================================================ */

let lightboxState = null;

export function initPostGalleries() {
  document.addEventListener('click', function (e) {
    var img = e.target.closest('.gallery-image');
    if (!img) return;

    var galleryId = img.dataset.galleryId;
    var images = document.querySelectorAll(
      '.gallery-image[data-gallery-id="' + galleryId + '"]'
    );
    var currentIndex = parseInt(img.dataset.index, 10);
    var imageUrls = Array.from(images).map(function (el) {
      return el.src;
    });

    openLightbox(imageUrls, currentIndex);
  });
}

function openLightbox(images, startIndex) {
  var overlay = document.createElement('div');
  overlay.className = 'lightbox-overlay';
  overlay.innerHTML =
    '<button class="lightbox-close" aria-label="Close">&times;</button>' +
    '<button class="lightbox-prev" aria-label="Previous">&#8249;</button>' +
    '<button class="lightbox-next" aria-label="Next">&#8250;</button>' +
    '<div class="lightbox-image-container"></div>' +
    '<div class="lightbox-counter"></div>';

  document.body.appendChild(overlay);
  document.body.style.overflow = 'hidden';

  lightboxState = {
    images: images,
    currentIndex: startIndex,
    overlay: overlay,
  };
  showImage(startIndex);

  // Close button
  overlay.querySelector('.lightbox-close').addEventListener(
    'click',
    closeLightbox
  );

  // Click on overlay background closes
  overlay.addEventListener('click', function (e) {
    if (e.target === overlay) closeLightbox();
  });

  // Prev / Next
  overlay.querySelector('.lightbox-prev').addEventListener('click', function () {
    navigateLightbox(-1);
  });
  overlay.querySelector('.lightbox-next').addEventListener('click', function () {
    navigateLightbox(1);
  });

  // Keyboard
  document.addEventListener('keydown', lightboxKeyHandler);
}

function showImage(index) {
  if (!lightboxState) return;
  var images = lightboxState.images;
  var container = lightboxState.overlay.querySelector(
    '.lightbox-image-container'
  );
  var counter = lightboxState.overlay.querySelector('.lightbox-counter');
  var prev = lightboxState.overlay.querySelector('.lightbox-prev');
  var next = lightboxState.overlay.querySelector('.lightbox-next');

  // Update image
  container.innerHTML =
    '<img src="' + encodeURI(images[index]) + '" alt="Gallery image">';

  // Update counter
  counter.textContent = index + 1 + ' / ' + images.length;

  // Show/hide prev/next
  prev.classList.toggle('hidden', index === 0);
  next.classList.toggle('hidden', index === images.length - 1);

  lightboxState.currentIndex = index;
}

function navigateLightbox(direction) {
  if (!lightboxState) return;
  var newIndex = lightboxState.currentIndex + direction;
  if (newIndex >= 0 && newIndex < lightboxState.images.length) {
    showImage(newIndex);
  }
}

function lightboxKeyHandler(e) {
  if (e.key === 'Escape') {
    closeLightbox();
  } else if (e.key === 'ArrowLeft') {
    navigateLightbox(-1);
  } else if (e.key === 'ArrowRight') {
    navigateLightbox(1);
  }
}

export function closeLightbox() {
  if (!lightboxState) return;
  document.removeEventListener('keydown', lightboxKeyHandler);
  lightboxState.overlay.remove();
  document.body.style.overflow = '';
  lightboxState = null;
}
