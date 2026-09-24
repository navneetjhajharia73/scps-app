let accessToken = null;

export function setToken(token) {
    accessToken = token;
}

export function getToken() {
    return accessToken;
}

export function clearToken() {
    accessToken = null;
}

export function isLoggedIn() {
    return accessToken !== null;
}

export async function authFetch(path) {
    const token = getToken();
    if (!token) {
        throw new Error("Not logged in");
    }

    const res = await fetch(path, {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });

    if (res.status === 401) {
        clearToken();
        window.location.reload();
        throw new Error("Session expired");
    }

    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Request failed");
    }

    return res.json();
}