/* ============================================================
   Stories module — Upload, display, viewer overlay
   ============================================================ */

import { getCookie } from './utils.js';

let currentUserStories = [];
let currentStoryIndex = 0;
let storyTimer = null;
const STORY_DURATION = 5000; // ms per story

export function initStories() {
  initStoryCircles();
  initStoryUpload();
  initViewerNav();
}

function initStoryUpload() {
  const form = document.getElementById('story-upload-form');
  if (!form) return;

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    const formData = new FormData(form);
    const fileInput = document.getElementById('story-image-input');
    if (!fileInput.files || !fileInput.files[0]) {
      alert('Please select an image.');
      return;
    }

    fetch('/stories/upload/', {
      method: 'POST',
      headers: { 'X-CSRFToken': getCookie('csrftoken') },
      body: formData,
    })
      .then(r => r.json())
      .then(data => {
        if (data.error) {
          alert(data.error);
        } else {
          const modal = document.getElementById('story-upload-modal');
          if (modal) modal.classList.add('hidden');
          form.reset();
          loadStoriesRow();
        }
      })
      .catch(() => alert('Failed to upload story.'));
  });
}

function loadStoriesRow() {
  fetch('/stories/row/')
    .then(r => r.text())
    .then(html => {
      const container = document.getElementById('stories-container');
      if (container) {
        container.innerHTML = html;
        initStoryCircles();
        initStoryUpload();
      }
    })
    .catch(() => {});
}

function initStoryCircles() {
  document.querySelectorAll('.story-circle[data-stories]').forEach(circle => {
    circle.addEventListener('click', function () {
      try {
        currentUserStories = JSON.parse(this.dataset.stories);
        if (!currentUserStories.length) return;
      } catch (e) {
        return;
      }
      currentStoryIndex = 0;
      openViewer(
        this.dataset.username,
        this.querySelector('.story-avatar')?.src || '',
      );
    });
  });

  document.querySelectorAll('#add-story-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const modal = document.getElementById('story-upload-modal');
      if (modal) modal.classList.remove('hidden');
    });
  });
}

function openViewer(username, avatarSrc) {
  const viewer = document.getElementById('story-viewer');
  if (!viewer) return;
  viewer.classList.remove('hidden');

  document.getElementById('story-viewer-username').textContent = username;
  const avatar = document.getElementById('story-viewer-avatar');
  if (avatar) avatar.src = avatarSrc;

  showStory(currentStoryIndex);
}

function showStory(index) {
  const story = currentUserStories[index];
  if (!story) {
    closeViewer();
    return;
  }

  const image = document.getElementById('story-viewer-image');
  const caption = document.getElementById('story-viewer-caption');
  const progress = document.getElementById('story-progress-bar');

  if (image) image.src = story.image_url;
  if (caption) caption.textContent = story.caption || '';
  if (caption) caption.style.display = story.caption ? 'block' : 'none';

  if (progress) {
    progress.style.transition = 'none';
    progress.style.width = '0%';
    void progress.offsetWidth; // force reflow
    progress.style.transition = 'width ' + STORY_DURATION + 'ms linear';
    progress.style.width = '100%';
  }

  clearTimeout(storyTimer);
  storyTimer = setTimeout(function () {
    if (currentStoryIndex < currentUserStories.length - 1) {
      currentStoryIndex++;
      showStory(currentStoryIndex);
    } else {
      closeViewer();
    }
  }, STORY_DURATION);
}

function closeViewer() {
  const viewer = document.getElementById('story-viewer');
  if (viewer) viewer.classList.add('hidden');
  clearTimeout(storyTimer);
  currentUserStories = [];
  currentStoryIndex = 0;
}

function initViewerNav() {
  const prevBtn = document.getElementById('story-prev');
  const nextBtn = document.getElementById('story-next');
  const closeBtn = document.getElementById('story-viewer-close');

  if (prevBtn) {
    prevBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      if (currentStoryIndex > 0) {
        currentStoryIndex--;
        showStory(currentStoryIndex);
      }
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      if (currentStoryIndex < currentUserStories.length - 1) {
        currentStoryIndex++;
        showStory(currentStoryIndex);
      } else {
        closeViewer();
      }
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener('click', closeViewer);
  }

  const viewer = document.getElementById('story-viewer');
  if (viewer) {
    viewer.addEventListener('click', function (e) {
      if (e.target === this) closeViewer();
    });
  }

  document.addEventListener('keydown', function (e) {
    const viewer = document.getElementById('story-viewer');
    if (!viewer || viewer.classList.contains('hidden')) return;

    if (e.key === 'Escape') {
      closeViewer();
    } else if (e.key === 'ArrowLeft' && currentStoryIndex > 0) {
      currentStoryIndex--;
      showStory(currentStoryIndex);
    } else if (e.key === 'ArrowRight') {
      if (currentStoryIndex < currentUserStories.length - 1) {
        currentStoryIndex++;
        showStory(currentStoryIndex);
      } else {
        closeViewer();
      }
    }
  });
}
