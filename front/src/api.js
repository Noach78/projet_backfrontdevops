export async function api(url, { method = "GET", body, token, signal } = {}) {
    const headers = {};
    if (body) headers["Content-Type"] = "application/json";
    if (token) headers.Authorization = `Bearer ${token}`;
    const json = body ? JSON.stringify(body) : undefined;
    const res = await fetch(url, { method, signal, headers, body: json });
    const data = res.status === 204 ? null : await res.json().catch(() => null);
    if (!res.ok) {
        const error = new Error(data?.message ?? `Erreur ${res.status}`);
        error.status = res.status;
        throw error;
    }
    return data;
}