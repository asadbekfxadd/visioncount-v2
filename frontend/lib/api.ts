/**
 * Тонкий клиент к VisionCount API.
 * Хранит JWT в localStorage и подставляет его в заголовок Authorization.
 */
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("vc_token");
}

export function setSession(token: string, user: unknown) {
  localStorage.setItem("vc_token", token);
  localStorage.setItem("vc_user", JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem("vc_token");
  localStorage.removeItem("vc_user");
}

export function getUser<T = any>(): T | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("vc_user");
  return raw ? (JSON.parse(raw) as T) : null;
}

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* no json body */
    }
    if (res.status === 401 && typeof window !== "undefined") {
      clearSession();
      window.location.href = "/login";
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string; user: any }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  dashboard: (params: { branch_id?: string; camera_id?: string } = {}) =>
    request<any>(`/dashboard?${new URLSearchParams(params as any)}`),

  companies: () => request<any[]>("/companies"),
  branches: () => request<any[]>("/branches"),
  createBranch: (data: any) =>
    request<any>("/branches", { method: "POST", body: JSON.stringify(data) }),

  cameras: () => request<any[]>("/cameras"),
  createCamera: (data: any) =>
    request<any>("/cameras", { method: "POST", body: JSON.stringify(data) }),
  updateCamera: (id: string, data: any) =>
    request<any>(`/cameras/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteCamera: (id: string) => request<void>(`/cameras/${id}`, { method: "DELETE" }),
  testCamera: (id: string) => request<any>(`/cameras/${id}/test`, { method: "POST" }),

  analyticsOverview: (branch_id?: string) =>
    request<any>(`/analytics${branch_id ? `?branch_id=${branch_id}` : ""}`),
  analyticsHourly: (branch_id?: string) =>
    request<any[]>(`/analytics/hourly${branch_id ? `?branch_id=${branch_id}` : ""}`),
  analyticsDaily: (days = 7, branch_id?: string) =>
    request<any[]>(
      `/analytics/daily?days=${days}${branch_id ? `&branch_id=${branch_id}` : ""}`
    ),
  analyticsHeatmap: (branch_id?: string) =>
    request<any[]>(`/analytics/heatmap${branch_id ? `?branch_id=${branch_id}` : ""}`),

  reports: () => request<any[]>("/reports"),
  createReport: (data: any) =>
    request<any>("/reports", { method: "POST", body: JSON.stringify(data) }),

  alerts: () => request<any[]>("/alerts"),
  users: () => request<any[]>("/users"),
  inviteUser: (data: any) =>
    request<any>("/users", { method: "POST", body: JSON.stringify(data) }),
};

export { API_URL };
