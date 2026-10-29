import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";
import CloseAccount from "./CloseAccount.jsx";

export default function AccountPage() {
  const { accountId, id } = useParams();
  const currentAccountId = accountId || id;
  const { token } = useAuth();

  const [account, setAccount] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    async function fetchAccount() {
      setIsLoading(true);
      setErrorMessage("");

      try {
        const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
        const data = await api(`${apiUrl}/account_info/${currentAccountId}`, {
          token,
        });

        setAccount(data.account);
      } catch (err) {
        setErrorMessage(
          err.message === "Account not found"
            ? "Ce compte n'existe pas ou n'a pas encore été ouvert."
            : err.message ||
                "Ce compte n'existe pas ou ne vous appartient pas.",
        );
      } finally {
        setIsLoading(false);
      }
    }

    if (currentAccountId) {
      fetchAccount();
    }
  }, [currentAccountId, token]);

  // loading
  if (isLoading) {
    return (
      <main className="account-page">
        <p>Chargement des détails du compte...</p>
      </main>
    );
  }

  // error
  if (errorMessage) {
    return (
      <main className="account-page">
        <section className="error-card" aria-labelledby="error-title">
          <h2 id="error-title">Compte inaccessible</h2>
          <p>{errorMessage}</p>
          <Link to="/" className="btn-secondary">
            Retour au tableau de bord
          </Link>
        </section>
      </main>
    );
  }

  // success
  const formattedBalance = new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
  }).format(account?.sold ?? 0);

  const formattedDate = account?.date_created
    ? new Date(account.date_created).toLocaleDateString("fr-FR")
    : "Date inconnue";

  const accountType = account?.type ?? "principal";

  return (
    <main className="account-page">
      <section className="account-card" aria-labelledby="account-title">
        <header className="account-header">
          <h1 id="account-title">Détail du compte</h1>
          <span className={`account-badge ${accountType}`}>
            Compte {accountType}
          </span>
        </header>

        <div className="account-details">
          <div className="detail-row">
            <span className="detail-label">Numéro de compte :</span>
            <span className="detail-value">{account?.account_id}</span>
          </div>

          <div className="detail-row">
            <span className="detail-label">Date d'ouverture :</span>
            <span className="detail-value">{formattedDate}</span>
          </div>

          <div className="balance-row">
            <span className="detail-label">Solde actuel :</span>
            <span className="balance-value">{formattedBalance}</span>
          </div>
        </div>

        <div className="account-actions">
          <Link to={`/deposit/${account?.account_id}`} className="btn-primary">
            {" "}
            Faire un dépôt{" "}
          </Link>
          <Link to="/transfer" className="btn-secondary">
            {" "}
            Faire un virement{" "}
          </Link>
          <Link
            to={`/accounts/${account?.account_id}/history`}
            className="btn-secondary"
          >
            {" "}
            Voir mes opérations{" "}
          </Link>
          <Link to="/" className="btn-secondary">
            {" "}
            Retour au tableau de bord{" "}
          </Link>

          <CloseAccount
            accountId={account.account_id}
            accountType={accountType}
          />
        </div>
      </section>
    </main>
  );
}
