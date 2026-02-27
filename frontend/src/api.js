// Centralized API base URL
// In production (Render), set REACT_APP_API_URL environment variable to your backend URL
// e.g. https://quotation-ai-backend.onrender.com
const BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default BASE;
