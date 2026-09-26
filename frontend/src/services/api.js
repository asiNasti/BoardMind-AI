const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  if (!response.ok) {
    let detail = 'Something went wrong. Please try again.';
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // Keep the generic message when the server response is not JSON.
    }
    throw new Error(detail);
  }
  return response.json();
}

export function listGames() {
  return request('/api/games/');
}

export function createGame(game) {
  return request('/api/games/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(game),
  });
}

export function uploadDocument(gameId, file) {
  const formData = new FormData();
  formData.append('file', file);
  return request(`/api/games/${gameId}/documents/`, {
    method: 'POST',
    body: formData,
  });
}

export function createChatSession(gameId) {
  return request('/api/chat/sessions/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ game_id: gameId }),
  });
}

export function listChatMessages(sessionId) {
  return request(`/api/chat/sessions/${sessionId}/messages/`);
}

export function sendChatMessage(sessionId, content) {
  return request(`/api/chat/sessions/${sessionId}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  });
}
