export async function api(url, { method = "GET", body, token, signal } = {}) {
    const headers = {};
    if (body) headers["Content-Type"] = "application/json";
    if (token) headers.Authorization = `Bearer ${token}`;
    const json = body ? JSON.stringify(body) : undefined;
    let res;
    try {
        res = await fetch(url, { method, signal, headers, body: json });
    } catch (requestError) {
        if (requestError instanceof TypeError) {
            throw new Error(
                `Impossible de contacter l'API (${url}). Vérifiez que le serveur FastAPI est démarré.`,
                { cause: requestError },
            );
        }
        throw requestError;
    }
    const data = res.status === 204 ? null : await res.json().catch(() => null);
    if (!res.ok) {
        const detail = data?.detail ?? data?.error ?? data?.message ?? data?.["Error !"];
        const message = Array.isArray(detail)
            ? detail.map((item) => item.msg).join(" ")
            : detail;
        const error = new Error(message ?? `Erreur ${res.status}`);
        error.status = res.status;
        throw error;
    }
    if (data?.error || data?.["Error !"]) {
        throw new Error(data.error ?? data["Error !"]);
    }
    return data;
}