/* ============================================================
   Messaging module — WebSocket Chat, Send, Search
   ============================================================ */

import { getCookie, escapeHtml, showToast } from './utils.js';

var chatSocket = null;
var pollInterval = null;

export function initChatWebSocket() {
  var chatArea = document.querySelector('.messages-container');
  if (!chatArea) return;

  var wsUrl = chatArea.getAttribute('data-websocket-url');
  if (!wsUrl) return;

  var conversationId = chatArea.getAttribute('data-conversation-id');
  var lastMessageId = parseInt(chatArea.getAttribute('data-last-message-id') || '0');

  function connect() {
    if (chatSocket && chatSocket.readyState === WebSocket.OPEN) return;

    var wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    var fullUrl = wsScheme + '://' + window.location.host + wsUrl;

    chatSocket = new WebSocket(fullUrl);

    chatSocket.onopen = function () {
      console.debug('Chat WebSocket connected');
      // Stop polling fallback if it was running
      if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
      }
    };

    chatSocket.onmessage = function (e) {
      try {
        var data = JSON.parse(e.data);

        if (data.type === 'new_message') {
          // Only append messages from others (own messages are already appended optimistically)
          if (!data.is_mine) {
            appendMessage({
              id: data.id,
              content: data.content,
              created_at: data.created_at,
              is_mine: false,
            });
            if (data.id > lastMessageId) lastMessageId = data.id;
            scrollToBottom();
          }
        } else if (data.type === 'typing') {
          showTypingIndicator(data.username, data.is_typing);
        }
      } catch (err) {
        console.error('Chat WS message error:', err);
      }
    };

    chatSocket.onclose = function () {
      console.debug('Chat WebSocket disconnected');
      startPollingFallback(conversationId);
    };

    chatSocket.onerror = function () {
      if (chatSocket) chatSocket.close();
    };
  }

  connect();
}

function startPollingFallback(conversationId) {
  if (pollInterval) return;

  var lastMessageId = parseInt(
    document.querySelector('.messages-container').getAttribute('data-last-message-id') || '0'
  );

  pollInterval = setInterval(function () {
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
  }, 3000);
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

  // Typing indicator
  var typingTimer = null;
  input.addEventListener('input', function () {
    if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
      chatSocket.send(JSON.stringify({
        type: 'typing',
        is_typing: true,
      }));
      clearTimeout(typingTimer);
      typingTimer = setTimeout(function () {
        if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
          chatSocket.send(JSON.stringify({
            type: 'typing',
            is_typing: false,
          }));
        }
      }, 1500);
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

  // Don't append if already present (check by id)
  if (msg.id && container.querySelector('[data-message-id="' + msg.id + '"]')) return;

  var div = document.createElement('div');
  div.className = 'message ' + (msg.is_mine ? 'sent' : 'received');
  if (msg.id) div.setAttribute('data-message-id', msg.id);

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

var typingTimeout = null;

function showTypingIndicator(username, isTyping) {
  var container = document.querySelector('.messages-container');
  if (!container) return;

  var existing = container.querySelector('.typing-indicator');
  if (isTyping) {
    if (!existing) {
      var div = document.createElement('div');
      div.className = 'message received typing-indicator';
      div.innerHTML =
        '<div class="message-bubble">' +
        '<div class="message-text"><em>' + escapeHtml(username) + ' is typing...</em></div>' +
        '</div>';
      container.appendChild(div);
      scrollToBottom();
    }
    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(function () {
      var el = container.querySelector('.typing-indicator');
      if (el) el.remove();
    }, 3000);
  } else {
    if (existing) existing.remove();
  }
}

export function initMessaging() {
  initChatWebSocket();
  initMessageSend();
  initConversationSearch();
}
