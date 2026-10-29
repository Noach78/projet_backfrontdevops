import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";

function getUserIdFromToken(token) {
  try {
    const payload = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    const decodedPayload = window.atob(payload);
    return decodedPayload.match(/"user_id"\s*:\s*(\d+)/)?.[1] ?? null;
  } catch {
    return null;
  }
}

export default function HomePage() {
  const { token } = useAuth();
  const [user, setUser] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const userId = token ? getUserIdFromToken(token) : null;
    if (!userId) {
      setError("Session invalide. Veuillez vous reconnecter.");
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
    Promise.all([
      api(`${apiUrl}/user_info/${userId}`, { token, signal: controller.signal }),
      api(`${apiUrl}/accounts/${userId}`, { token, signal: controller.signal }),
    ])
      .then(([userData, accountData]) => {
        setUser(userData);
        setAccounts(accountData.accounts ?? []);
      })
      .catch((requestError) => {
        if (requestError.name !== "AbortError") setError(requestError.message);
      })
      .finally(() => setLoading(false));

    return () => controller.abort();
  }, [token]);

  return (
    <main>
      <h1>Bienvenue</h1>
      {loading ? (
        <p role="status">Chargement de votre profil…</p>
      ) : error ? (
        <p role="alert">{error}</p>
      ) : (
        <p>Email connecté : <strong>{user?.email}</strong></p>
      )}

      <p>Nombre de comptes : <strong>{accounts.length}</strong></p>
      <p>Solde totale : <strong>{accounts.reduce((total, account) => total + account.sold, 0)}</strong> €</p>

      <nav aria-label="Actions sur les comptes">
        <ul>
          <li><Link to="/accounts">La liste de mes comptes</Link></li>
          <li><Link to="/accounts/new">Ouvrir un nouveau compte</Link></li>
        </ul>
      </nav>
    </main>
  );
}
