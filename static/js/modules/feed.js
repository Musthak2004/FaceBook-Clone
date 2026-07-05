/* ============================================================
   Feed module — Like, Save, Comment, Infinite Scroll, Post Modal
   ============================================================ */

import { getCookie, showToast } from './utils.js';
import { openModal, closeModal } from './ui.js';

export function initLikeButtons() {
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

export function initSaveButtons() {
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

export function initCommentForms() {
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
            var commentsList = document.querySelector(
              '.post-comments[data-post-id="' + postId + '"]'
            );
            if (commentsList && data.html) {
              commentsList.insertAdjacentHTML('beforeend', data.html);
            }
            input.value = '';
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

export function initInfiniteScroll() {
  var sentinel = document.querySelector('.infinite-scroll-sentinel');
  if (!sentinel) return;

  var page = 1;
  var loading = false;
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

export function initCreatePostModal() {
  var createBtn = document.querySelector('.create-post-input');
  if (createBtn) {
    createBtn.addEventListener('click', function () {
      var modal = document.getElementById('create-post-modal');
      if (modal) {
        // Dispatch custom event for modal open
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
      }
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

export function initShareButtons() {
  var csrftoken = getCookie('csrftoken');
  var currentPostId = null;

  // Show share modal
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.share-btn');
    if (!btn) return;
    var postId = btn.getAttribute('data-post-id');
    var postUrl = btn.getAttribute('data-post-url');
    currentPostId = postId;
    var modal = document.getElementById('share-modal');
    modal.dataset.sharePostId = postId;
    modal.dataset.sharePostUrl = postUrl;
    // Clear previous content
    document.getElementById('share-repost-content').value = '';
    openModal(modal);
  });

  // Repost submit
  document.getElementById('share-repost-submit').addEventListener('click', function () {
    var modal = document.getElementById('share-modal');
    var postId = modal.dataset.sharePostId;
    var content = document.getElementById('share-repost-content').value.trim();
    var visibility = document.getElementById('share-repost-visibility').value;

    var body = 'visibility=' + encodeURIComponent(visibility);
    if (content) {
      body += '&content=' + encodeURIComponent(content);
    }

    fetch('/posts/' + postId + '/share/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrftoken,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: body,
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.shared) {
          closeModal(modal);
          showToast('Post shared to your timeline!');
        }
      })
      .catch(function (err) { console.error('Share error:', err); });
  });

  // Copy link
  document.getElementById('share-copy-btn').addEventListener('click', function () {
    var modal = document.getElementById('share-modal');
    var url = window.location.origin + modal.dataset.sharePostUrl;
    navigator.clipboard.writeText(url).then(function () {
      closeModal(modal);
      showToast('Link copied to clipboard!');
    }).catch(function () {
      // Fallback for older browsers
      var textarea = document.createElement('textarea');
      textarea.value = url;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      closeModal(modal);
      showToast('Link copied to clipboard!');
    });
  });
}

export function initPollVoting() {
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.poll-option:not(:disabled)');
    if (!btn) return;

    var optionId = btn.getAttribute('data-option-id');
    var pollEl = btn.closest('.post-poll');
    var pollId = pollEl.getAttribute('data-poll-id');
    var csrfToken = getCookie('csrftoken');

    fetch('/posts/' + pollId + '/vote/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: 'option_id=' + encodeURIComponent(optionId),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.voted) {
          // Disable all options
          pollEl.querySelectorAll('.poll-option').forEach(function (opt) {
            opt.disabled = true;
          });

          // Update bars and percentages
          data.options.forEach(function (opt) {
            var optBtn = pollEl.querySelector(
              '.poll-option[data-option-id="' + opt.id + '"]'
            );
            if (!optBtn) return;
            optBtn.setAttribute('data-votes', opt.vote_count);
            optBtn.setAttribute('data-pct', opt.percentage);
            optBtn.querySelector('.poll-option-pct').textContent = opt.percentage + '%';
            optBtn.querySelector('.poll-option-bar').style.width = opt.percentage + '%';
          });

          // Update total votes
          var footer = pollEl.querySelector('.poll-total-votes');
          if (footer) {
            footer.textContent = data.total_votes + ' vote' + (data.total_votes !== 1 ? 's' : '');
            footer.setAttribute('data-total', data.total_votes);
          }

          // Show "You voted"
          var footerEl = pollEl.querySelector('.poll-footer');
          var youVoted = footerEl.querySelector('.you-voted');
          if (!youVoted) {
            var span = document.createElement('span');
            span.className = 'text-muted you-voted';
            span.style.cssText = 'font-size:var(--font-size-xs);';
            span.textContent = 'You voted';
            footerEl.appendChild(span);
          }

          showToast('Vote recorded!');
        }
      })
      .catch(function (err) { console.error('Poll vote error:', err); });
  });
}

export function initFeed() {
  initLikeButtons();
  initSaveButtons();
  initCommentForms();
  initInfiniteScroll();
  initCreatePostModal();
  initShareButtons();
  initPollVoting();
}
