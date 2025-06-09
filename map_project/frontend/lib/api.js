// frontend/lib/api.js
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'; // Assurez-vous que le port correspond à votre backend

export async function fetchApi(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = typeof window !== 'undefined' ? localStorage.getItem('authToken') : null;

  const defaultHeaders = {
    'Content-Type': 'application/json',
  };

  const headers = {
    ...defaultHeaders,
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let body = options.body;

  // Stringify body if it's an object and Content-Type is application/json
  if (body && typeof body !== 'string' && headers['Content-Type'] === 'application/json') {
    body = JSON.stringify(body);
  }

  // For x-www-form-urlencoded, body should already be URLSearchParams or string.
  // No special handling needed here for it, assuming it's prepared by caller.

  try {
    const response = await fetch(url, { ...options, headers, body });

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch (e) {
        // If response is not JSON (e.g. plain text error from proxy or server)
        errorData = { detail: response.statusText || 'Erreur API inconnue.' };
      }

      const error = new Error(errorData.detail || 'Une erreur API est survenue.');
      error.status = response.status;
      error.data = errorData; // Attach full error data if available
      throw error;
    }

    // Handle 204 No Content or other responses that might not have JSON body
    if (response.status === 204) {
        return null; // Or some indication of success with no content
    }

    // Try to parse JSON if content-type suggests it, otherwise return response (e.g. for text())
    const contentType = response.headers.get("content-type");
    if (contentType?.includes("application/json")) {
        return await response.json();
    }

    // For non-JSON responses, or if content-type is missing but body might exist (e.g. plain text)
    // This part might need adjustment based on expected non-JSON responses.
    // For now, returning the raw response object might be too much.
    // Consider response.text() if plain text is a possibility.
    // If primarily JSON or 204, the above checks are key.
    return response; // Fallback, could be response.text()

  } catch (error) {
    // Log generic error only if it's not an HTTP error we already processed
    if (!error.status) {
        console.error('API call failed (network or other error):', error);
    }
    throw error; // Rethrow for the calling component to handle
  }
}
