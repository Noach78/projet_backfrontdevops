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
  const userId = token ? getUserIdFromToken(token) : null;
  const [user, setUser] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!userId) {
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
  }, [token, userId]);

  return (
    <section className="dashboard-page">
      <header className="page-heading dashboard-heading">
        <div>
          <p className="eyebrow">Votre espace bancaire</p>
          <h1>Bienvenue{user?.email ? `, ${user.email}` : ""}</h1>
          <p>Retrouvez en un coup d’œil la situation de vos comptes.</p>
        </div>
        <Link className="button button-primary" to="/accounts/new">
          Ouvrir un compte
        </Link>
      </header>

      {!userId ? (
        <p className="status-card status-error" role="alert">
          Session invalide. Veuillez vous reconnecter.
        </p>
      ) : loading ? (
        <p className="status-card" role="status">Chargement de votre profil…</p>
      ) : error ? (
        <p className="status-card status-error" role="alert">{error}</p>
      ) : (
        <div className="dashboard-metrics">
          <article className="metric-card">
            <span className="metric-label">Comptes actifs</span>
            <strong className="metric-value">{accounts.length}</strong>
            <span className="metric-note">dans votre espace</span>
          </article>
          <article className="metric-card metric-card-highlight">
            <span className="metric-label">Solde total</span>
            <strong className="metric-value">
              {new Intl.NumberFormat("fr-FR", {
                style: "currency",
                currency: "EUR",
              }).format(accounts.reduce((total, account) => total + account.sold, 0))}
            </strong>
            <span className="metric-note">tous comptes confondus</span>
          </article>
        </div>
      )}

      <section className="dashboard-actions" aria-labelledby="actions-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Accès rapide</p>
            <h2 id="actions-title">Que souhaitez-vous faire ?</h2>
          </div>
        </div>
        <div className="action-grid">
          <Link className="action-card" to="/accounts">
            <span className="action-icon" aria-hidden="true">01</span>
            <span><strong>Mes comptes</strong><small>Consulter vos comptes et soldes</small></span>
            <span className="action-arrow" aria-hidden="true">→</span>
          </Link>
          <Link className="action-card" to="/transfer">
            <span className="action-icon" aria-hidden="true">02</span>
            <span><strong>Effectuer un virement</strong><small>Envoyer de l’argent à un bénéficiaire</small></span>
            <span className="action-arrow" aria-hidden="true">→</span>
          </Link>
          <Link className="action-card" to="/beneficiaries">
            <span className="action-icon" aria-hidden="true">03</span>
            <span><strong>Mes bénéficiaires</strong><small>Retrouver les bénéficiaires enregistrés</small></span>
            <span className="action-arrow" aria-hidden="true">→</span>
          </Link>
        </div>
      </section>
    </section>
  );
}
