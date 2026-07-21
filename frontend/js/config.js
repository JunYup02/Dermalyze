/**
 * Single place to point the frontend at a backend deployment.
 *
 * Points at the deployed Render backend by default. For local frontend dev
 * against a local backend, run `uvicorn app.main:app --reload` in backend/
 * and either edit DEFAULT_API_BASE_URL below or run
 * `localStorage.setItem('dermalyze_api_base', 'http://127.0.0.1:8000')`
 * in the browser console — the localStorage override always wins.
 */
const DEFAULT_API_BASE_URL = "https://dermalyze-api.onrender.com";

const API_BASE_URL = (
  localStorage.getItem("dermalyze_api_base") || DEFAULT_API_BASE_URL
).replace(/\/+$/, "");
