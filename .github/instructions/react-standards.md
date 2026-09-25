---
name: React Production Standards
description: Universal guidelines for frontend React code - components, state management, and API integration.
applyTo: "frontend/src/**/*.js, frontend/src/**/*.jsx"
---

# React Production Standards

These standards define the rules for generating clean, modern, and maintainable frontend code using React. The goal is to keep the frontend as simple and readable as possible.

## Design Principles

- **Modern React Only:** Strictly use Functional Components and React Hooks (`useState`, `useEffect`, `useRef`). NEVER use Class Components or legacy lifecycle methods.
- **Keep it Simple:** Do not introduce complex global state management libraries (like Redux or MobX) unless strictly necessary. Use React Context or simple state lifting for this project.
- **Separation of Concerns:** UI components must NOT contain raw `fetch()` or `axios` calls. All API communication must be encapsulated in a dedicated `services/api.js` file.

## Topic: Component Structure & Styling

- **File Naming:** Use `PascalCase` for component files (e.g., `ChatWindow.jsx`, `UploadModal.jsx`).
- **Styling:** Use standard CSS modules or Tailwind CSS (if configured). Avoid heavy CSS-in-JS libraries for this MVP. Do not use inline styles (`style={{...}}`) for complex layouts.
- **Props Validation:** If using plain JavaScript, ensure props are documented. Keep component props minimal to avoid "prop drilling".

## Topic: API Integration & Error Handling

- **API Client:** Use a centralized API service (e.g., `api.js`) that defines base URLs and handles common headers (like `Content-Type: application/json`).
- **Loading States:** Always implement and display loading states (e.g., spinners or disabled buttons) during async operations like PDF uploading or waiting for AI RAG responses.
- **Error Handling:** Gracefully handle backend errors. If the FastAPI backend returns a 400 or 422 error, display a clear, user-friendly error message in the UI, not an alert box or console dump.

## Anti-patterns

- **Direct DOM Manipulation:** Never use `document.getElementById` or `document.querySelector`. Always use React state and `useRef`.
- **Spaghetti API Calls:** Calling `fetch` directly inside an `onClick` handler inside a component return block. 
- **Missing Loading States:** Freezing the UI without feedback while the backend processes embeddings or LLM responses.

## Example: Clean API Encapsulation

### BAD (API call mixed with UI)
```javascript
function UploadButton() {
  const handleUpload = async () => {
    const response = await fetch('http://localhost:8000/api/games/1/documents/', { method: 'POST', body: ... });
    // messy UI update
  };
  return <button onClick={handleUpload}>Upload</button>;
}
```

### GOOD (Delegated to service)
```javascript
// services/api.js
export const uploadDocument = async (gameId, formData) => {
  return await fetch(`/api/games/${gameId}/documents/`, { method: 'POST', body: formData });
};

// components/UploadButton.jsx
import { uploadDocument } from '../services/api';

function UploadButton({ gameId }) {
  const [isLoading, setIsLoading] = useState(false);

  const handleUpload = async (formData) => {
    setIsLoading(true);
    try {
      await uploadDocument(gameId, formData);
      // Success handling
    } catch (error) {
      // Error handling
    } finally {
      setIsLoading(false);
    }
  };

  return <button onClick={handleUpload} disabled={isLoading}>Upload</button>;
}
```
