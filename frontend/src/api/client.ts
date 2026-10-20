import axios from "axios";

export const LOGIN_URL = "/auth/login";

const client = axios.create({
  baseURL: "/api",
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (res) => res,
  (err) => {
    // A 401 means the session has expired, except from the login form itself, where it means
    // a wrong password: the form shows that message, so don't reload the page over it.
    if (err.response?.status === 401 && err.config?.url !== LOGIN_URL) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export default client;

/** The API's error message for a failed request, or `fallback` if it didn't send a readable one. */
export function errorMessage(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err)) {
    const detail: unknown = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return fallback;
}
