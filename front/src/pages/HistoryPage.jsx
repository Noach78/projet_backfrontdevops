import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";

const dateFormatter = new Intl.DateTimeFormat("fr-FR", {
  dateStyle: "medium",
  timeStyle: "short",
});
const amountFormatter = new Intl.NumberFormat("fr-FR", {
  style: "currency",
  currency: "EUR",
});

export default function HistoryPage() {
  const { accountId } = useParams();
  const { token } = useAuth();
  const [transactions, setTransactions] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
    api(`${apiUrl}/transaction_history/${accountId}`, {
      method: "POST",
      token,
      signal: controller.signal,
    })
      .then((data) => setTransactions(data.transactions ?? []))
      .catch((err) => { if (err.name !== "AbortError") setError(err.message); })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [accountId, token]);

  return (
    <section className="history-page">
      <header className="page-heading">
        <div>
          <p className="eyebrow">Activité du compte</p>
          <h1>Historique des opérations</h1>
          <p>Compte n° {accountId}</p>
        </div>
        <Link className="button button-secondary" to={`/accounts/${accountId}`}>Retour au compte</Link>
      </header>
      {loading ? <p role="status">Chargement des transactions…</p>
        : error ? <p role="alert">{error}</p>
          : transactions.length === 0 ? <p>Aucune transaction pour ce compte.</p>
            : (
              <ol className="transactions-list" aria-label="Transactions, de la plus récente à la plus ancienne">
                {transactions.map((transaction) => {
                  const outgoing = String(transaction.source) === String(accountId);
                  return (
                    <li key={transaction.transaction_id}>
                      <article>
                        <h2>{outgoing ? "Débit" : "Crédit"}{transaction.is_cancelled ? " — annulée" : ""}</h2>
                        <p>Montant : {amountFormatter.format(transaction.amount)}</p>
                        <p>Date : {dateFormatter.format(new Date(transaction.created_at))}</p>
                        <p>Compte source : n° {transaction.source}</p>
                        <p>Destinataire : n° {transaction.recipient}</p>
                      </article>
                    </li>
                  );
                })}
              </ol>
            )}
    </section>
  );
}
