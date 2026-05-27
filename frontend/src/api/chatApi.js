import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 90000, // 90s timeout to allow for Render cold starts
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Send a chat message and get a response from the RAG pipeline.
 * @param {string} message - User's question
 * @param {string} [sessionId] - Optional session ID
 * @returns {Promise<{answer: string, sources: Array, found_context: boolean}>}
 */
export async function sendMessage(message, sessionId = null) {
  const payload = {
    message,
    ...(sessionId && { session_id: sessionId }),
  };

  const response = await api.post('/api/chat', payload);
  return response.data;
}

/**
 * Check the API health status.
 * @returns {Promise<{status: string, chunks_in_db: number, model_loaded: boolean}>}
 */
export async function getHealth() {
  const response = await api.get('/api/health');
  return response.data;
}

export default api;
