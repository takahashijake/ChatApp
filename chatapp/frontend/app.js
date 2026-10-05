const joinView = document.querySelector("#join-view");
const chatView = document.querySelector("#chat-view");
const joinForm = document.querySelector("#join-form");
const joinButton = document.querySelector("#join-button");
const usernameInput = document.querySelector("#username");
const joinError = document.querySelector("#join-error");
const messageForm = document.querySelector("#message-form");
const messageInput = document.querySelector("#message-input");
const messageCount = document.querySelector("#message-count");
const messageList = document.querySelector("#message-list");
const messageRegion = document.querySelector("#message-region");
const emptyState = document.querySelector("#empty-state");
const profileName = document.querySelector("#profile-name");
const profileAvatar = document.querySelector("#profile-avatar");
const leaveButton = document.querySelector("#leave-button");
const connectionPill = document.querySelector("#connection-pill");
const connectionLabel = document.querySelector("#connection-label");
const toastRegion = document.querySelector("#toast-region");

const usernamePattern = /^[A-Za-z0-9_.-]{1,32}$/;

let socket = null;
let username = "";
let hasJoined = false;

function websocketUrl(name) {
  const scheme = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${scheme}//${window.location.host}/ws?name=${encodeURIComponent(name)}`;
}

function setJoining(isJoining) {
  joinButton.disabled = isJoining;
  joinButton.querySelector("span").textContent = isJoining ? "Connecting…" : "Enter general";
}

function setConnectionState(state, label) {
  connectionPill.dataset.state = state;
  connectionLabel.textContent = label;
}

function showToast(message, tone = "neutral") {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.dataset.tone = tone;
  toast.textContent = message;
  toastRegion.append(toast);
  window.setTimeout(() => toast.remove(), 3600);
}

function clearMessages() {
  messageList.replaceChildren();
  emptyState.hidden = false;
}

function scrollToLatest() {
  window.requestAnimationFrame(() => {
    messageRegion.scrollTop = messageRegion.scrollHeight;
  });
}

function formatTime(date = new Date()) {
  return new Intl.DateTimeFormat([], {
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function splitMessage(text) {
  const separator = text.indexOf(": ");
  if (separator <= 0) {
    return { sender: "Message", body: text };
  }

  return {
    sender: text.slice(0, separator),
    body: text.slice(separator + 2),
  };
}

function appendMessage({ sender, body, own = false }) {
  emptyState.hidden = true;

  const row = document.createElement("article");
  row.className = `message-row${own ? " own-message" : ""}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar message-avatar";
  avatar.textContent = sender.slice(0, 1).toUpperCase() || "?";

  const content = document.createElement("div");
  content.className = "message-content";

  const meta = document.createElement("div");
  meta.className = "message-meta";

  const author = document.createElement("strong");
  author.textContent = own ? `${sender} · you` : sender;

  const time = document.createElement("time");
  time.dateTime = new Date().toISOString();
  time.textContent = formatTime();

  const text = document.createElement("p");
  text.textContent = body;

  meta.append(author, time);
  content.append(meta, text);
  row.append(avatar, content);
  messageList.append(row);
  scrollToLatest();
}

function appendSystemMessage(text) {
  emptyState.hidden = true;

  const row = document.createElement("div");
  row.className = "system-message";

  const marker = document.createElement("span");
  marker.className = "system-marker";
  marker.setAttribute("aria-hidden", "true");
  marker.textContent = "•";

  const body = document.createElement("span");
  body.textContent = text.replace(/^\[Server\]\s*/, "");

  const time = document.createElement("time");
  time.dateTime = new Date().toISOString();
  time.textContent = formatTime();

  row.append(marker, body, time);
  messageList.append(row);
  scrollToLatest();
}

function enterChat(name) {
  username = name;
  hasJoined = true;
  joinView.hidden = true;
  chatView.hidden = false;
  profileName.textContent = name;
  profileAvatar.textContent = name.slice(0, 1).toUpperCase();
  setConnectionState("online", "Online");
  clearMessages();
  appendSystemMessage(`Connected as @${name}`);
  messageInput.focus();
}

function returnToJoin(message = "") {
  hasJoined = false;
  chatView.hidden = true;
  joinView.hidden = false;
  setJoining(false);
  if (message) {
    joinError.textContent = message;
  }
  usernameInput.focus();
}

function closeSocket() {
  if (socket) {
    const current = socket;
    socket = null;
    current.onclose = null;
    current.close(1000, "Client left");
  }
}

function connect(name) {
  closeSocket();
  joinError.textContent = "";
  setJoining(true);
  setConnectionState("connecting", "Connecting");

  socket = new WebSocket(websocketUrl(name));

  socket.addEventListener("message", (event) => {
    let payload;
    try {
      payload = JSON.parse(event.data);
    } catch {
      showToast("Received an invalid server response.", "danger");
      return;
    }

    if (payload.type === "connected") {
      setJoining(false);
      enterChat(payload.name);
      return;
    }

    if (payload.type === "message") {
      appendMessage(splitMessage(payload.text));
      return;
    }

    if (payload.type === "system") {
      appendSystemMessage(payload.text);
      return;
    }

    if (payload.type === "error") {
      if (hasJoined) {
        showToast(payload.message, "danger");
      } else {
        joinError.textContent = payload.message;
        setJoining(false);
      }
      return;
    }

    if (payload.type === "disconnected") {
      setConnectionState("offline", "Offline");
      appendSystemMessage(payload.message || "Connection closed.");
    }
  });

  socket.addEventListener("close", () => {
    const wasJoined = hasJoined;
    socket = null;
    setJoining(false);

    if (wasJoined) {
      setConnectionState("offline", "Offline");
      appendSystemMessage("Connection ended. Leave and rejoin to reconnect.");
      messageInput.disabled = true;
      showToast("Disconnected from ChatApp.", "danger");
    }
  });

  socket.addEventListener("error", () => {
    if (!hasJoined) {
      joinError.textContent = "Unable to open a connection to ChatApp.";
      setJoining(false);
    }
  });
}

joinForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const candidate = usernameInput.value.trim();

  if (!usernamePattern.test(candidate)) {
    joinError.textContent =
      "Use 1–32 characters: letters, numbers, period, underscore, or hyphen.";
    return;
  }

  connect(candidate);
});

messageForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = messageInput.value.trim();

  if (!text || !socket || socket.readyState !== WebSocket.OPEN) {
    return;
  }

  socket.send(JSON.stringify({ type: "message", text }));
  appendMessage({ sender: username, body: text, own: true });
  messageInput.value = "";
  messageCount.textContent = "0 / 4000";
});

messageInput.addEventListener("input", () => {
  messageCount.textContent = `${messageInput.value.length} / 4000`;
});

leaveButton.addEventListener("click", () => {
  closeSocket();
  messageInput.disabled = false;
  clearMessages();
  usernameInput.value = username;
  username = "";
  returnToJoin();
});

window.addEventListener("beforeunload", closeSocket);
