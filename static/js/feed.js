/* ============================================================
   Feed JavaScript — Like, Comment, Save, Infinite Scroll
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {
  initLikeButtons();
  initSaveButtons();
  initCommentForms();
  initInfiniteScroll();
  initCreatePostModal();
});

/* ---- Like / React Button ---- */
function initLikeButtons() {
  document.querySelectorAll('.post-action-like').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      var postId = this.getAttribute('data-post-id');
      var csrfToken = getCookie('csrftoken');

      fetch('/reactions/' + postId + '/like/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken,
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'reaction_type=like',
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.liked) {
            btn.classList.add('liked');
          } else {
            btn.classList.remove('liked');
          }
          var countEl = btn.querySelector('.like-count');
          if (countEl) countEl.textContent = data.total_likes;
        })
        .catch(function (err) { console.error('Like error:', err); });
    });
  });
}

/* ---- Save Post ---- */
function initSaveButtons() {
  document.querySelectorAll('.post-action-save').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      var postId = this.getAttribute('data-post-id');
      var csrfToken = getCookie('csrftoken');

      fetch('/posts/' + postId + '/save/', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken },
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.saved) {
            btn.classList.add('saved');
            showToast('Post saved');
          } else {
            btn.classList.remove('saved');
            showToast('Post unsaved');
          }
        })
        .catch(function (err) { console.error('Save error:', err); });
    });
  });
}

/* ---- Comment Form ---- */
function initCommentForms() {
  document.querySelectorAll('.comment-form').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var input = this.querySelector('input[name="content"]');
      var content = input.value.trim();
      if (!content) return;

      var postId = this.getAttribute('data-post-id');
      var csrfToken = getCookie('csrftoken');

      fetch('/posts/' + postId + '/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken,
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'content=' + encodeURIComponent(content) + '&action=comment',
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.created) {
            // Add comment to the list
            var commentsList = document.querySelector(
              '.post-comments[data-post-id="' + postId + '"]'
            );
            if (commentsList && data.html) {
              commentsList.insertAdjacentHTML('beforeend', data.html);
            }
            input.value = '';
            // Update comment count
            var countEl = document.querySelector(
              '.comment-count[data-post-id="' + postId + '"]'
            );
            if (countEl) countEl.textContent = data.total_comments;
          }
        })
        .catch(function (err) { console.error('Comment error:', err); });
    });
  });
}

/* ---- Infinite Scroll ---- */
function initInfiniteScroll() {
  var sentinel = document.querySelector('.infinite-scroll-sentinel');
  if (!sentinel) return;

  var page = 1;
  var loading = false;

  /* Only start observing if there's a next page on initial load */
  var nextLink = document.querySelector('.pagination .next');
  if (!nextLink) {
    sentinel.classList.add('hidden');
    return;
  }

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting && !loading) {
        loading = true;
        page++;
        var url = window.location.pathname + '?page=' + page;

        fetch(url, {
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
          .then(function (r) { return r.text(); })
          .then(function (html) {
            var temp = document.createElement('div');
            temp.innerHTML = html;
            var newPosts = temp.querySelector('.feed-container');
            if (newPosts) {
              var container = document.querySelector('.feed-container');
              container.insertAdjacentHTML('beforeend', newPosts.innerHTML);
            }
            loading = false;

            // Check if there are more pages
            var nextLink = temp.querySelector('.pagination .next');
            if (!nextLink) {
              sentinel.classList.add('hidden');
            }
          })
          .catch(function () { loading = false; });
      }
    });
  });

  observer.observe(sentinel);
}

/* ---- Create Post Modal ---- */
function initCreatePostModal() {
  var createBtn = document.querySelector('.create-post-input');
  if (createBtn) {
    createBtn.addEventListener('click', function () {
      var modal = document.getElementById('create-post-modal');
      if (modal) openModal(modal);
    });
  }

  var postForm = document.getElementById('create-post-form');
  if (postForm) {
    postForm.addEventListener('submit', function (e) {
      var content = this.querySelector('textarea[name="content"]').value.trim();
      if (!content) {
        e.preventDefault();
        showToast('Please write something before posting');
      }
    });
  }
}
