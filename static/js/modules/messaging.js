/* ============================================================
   Messaging module — Chat Polling, Send, Search
   ============================================================ */

import { getCookie, escapeHtml } from './utils.js';

export function initChatPolling() {
  var chatArea = document.querySelector('.messages-container');
  if (!chatArea) return;

  var conversationId = chatArea.getAttribute('data-conversation-id');
  var lastMessageId = parseInt(chatArea.getAttribute('data-last-message-id') || '0');

  function pollMessages() {
    fetch('/messages/' + conversationId + '/?since=' + lastMessageId, {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.messages && data.messages.length > 0) {
          data.messages.forEach(function (msg) {
            appendMessage(msg);
            if (msg.id > lastMessageId) lastMessageId = msg.id;
          });
          scrollToBottom();
        }
      })
      .catch(function () {});
  }

  setInterval(pollMessages, 3000);
}

export function initMessageSend() {
  var form = document.querySelector('.message-input-area');
  if (!form) return;

  var input = form.querySelector('.message-input');
  var sendBtn = form.querySelector('.message-send-btn');
  var conversationId = form.getAttribute('data-conversation-id');
  var csrfToken = getCookie('csrftoken');

  function sendMessage() {
    var content = input.value.trim();
    if (!content) return;

    sendBtn.disabled = true;

    fetch('/messages/' + conversationId + '/send/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: 'content=' + encodeURIComponent(content),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.sent) {
          appendMessage({
            id: Date.now(),
            content: data.content,
            created_at: data.created_at,
            is_mine: true,
          });
          input.value = '';
          scrollToBottom();
        }
      })
      .catch(function (err) { console.error('Send error:', err); })
      .finally(function () { sendBtn.disabled = false; });
  }

  sendBtn.addEventListener('click', sendMessage);
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
}

export function initConversationSearch() {
  var searchInput = document.querySelector('.conversation-search input');
  if (!searchInput) return;

  searchInput.addEventListener('input', function () {
    var query = this.value.toLowerCase().trim();
    document.querySelectorAll('.conversation-item').forEach(function (item) {
      var name = item.querySelector('.conversation-item-name');
      if (name) {
        var match = name.textContent.toLowerCase().indexOf(query) !== -1;
        item.style.display = match || !query ? 'flex' : 'none';
      }
    });
  });
}

function appendMessage(msg) {
  var container = document.querySelector('.messages-container');
  if (!container) return;

  var div = document.createElement('div');
  div.className = 'message ' + (msg.is_mine ? 'sent' : 'received');

  div.innerHTML =
    '<div class="message-bubble">' +
    '<div class="message-text">' + escapeHtml(msg.content) + '</div>' +
    '<div class="message-time">' + formatTime(msg.created_at) + '</div>' +
    '</div>';

  container.appendChild(div);
}

function scrollToBottom() {
  var container = document.querySelector('.messages-container');
  if (container) {
    container.scrollTop = container.scrollHeight;
  }
}

function formatTime(dateString) {
  var date = new Date(dateString);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export function initMessaging() {
  initChatPolling();
  initMessageSend();
  initConversationSearch();
}
