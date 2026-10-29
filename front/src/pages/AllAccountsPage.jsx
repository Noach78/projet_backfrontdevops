import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";

const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export default function AllAccountsPage() {
    const { token } = useAuth();
    const [accounts, setAccounts] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [errorMessage, setErrorMessage] = useState("");

    useEffect(() => {
        let active = true;

        async function fetchAccounts() {
            setIsLoading(true);
            setErrorMessage("");

            try {
                const data = await api(`${apiUrl}/my_accounts`, { token });
                if (active) {
                    const sorted = [...(data.accounts || [])].sort(
                        (a, b) => new Date(b.date_created) - new Date(a.date_created)
                    );
                    setAccounts(sorted);
                }
            } catch (err) {
                if (active) {
                    setErrorMessage(
                        err.message || "Impossible de charger vos comptes bancaires."
                    );
                }
            } finally {
                if (active) {
                    setIsLoading(false);
                }
            }
        }

        if (token) {
            fetchAccounts();
        }
        return () => {
            active = false;
        };
    }, [token]);

    //loading 
    if (isLoading) {
        return (
            <main className="all-accounts-page">
                <div className="loading-state">
                    <p>Chargement de vos comptes...</p>
                </div>
            </main>
        );
    }

    //error 
    if (errorMessage) {
        return (
            <main className="all-accounts-page">
                <section className="error-card" aria-labelledby="error-title">
                    <h2 id="error-title">Erreur lors de la récupération des comptes</h2>
                    <p>{errorMessage}</p>
                    <Link to="/" className="btn-secondary">
                        Retour à l'accueil
                    </Link>
                </section>
            </main>
        );
    }

    //vide
    if (accounts.length === 0) {
        return (
            <main className="all-accounts-page">
                <header className="all-accounts-header">
                    <h1>Mes comptes</h1>
                </header>
                <div className="empty-state">
                    <p>Vous ne possédez aucun compte bancaire pour le moment.</p>
                    <Link to="/" className="btn-secondary">
                        Retour à l'accueil
                    </Link>
                </div>
            </main>
        );
    }

    //success
    return (
        <main className="all-accounts-page">
            <header className="all-accounts-header">
                <h1>Mes comptes</h1>
            </header>

            <div className="accounts-grid">
                {accounts.map((account) => {
                    const formattedBalance = new Intl.NumberFormat("fr-FR", {
                        style: "currency",
                        currency: "EUR",
                    }).format(account.sold ?? 0);

                    const formattedDate = account.date_created
                        ? new Date(account.date_created).toLocaleDateString("fr-FR")
                        : "N/A";

                    const accountType = account.type ?? "principal";

                    return (
                        <div key={account.account_id} className="account-item-card">
                            <div className="card-top">
                                <span className={`account-badge ${accountType}`}>
                                    Compte {accountType}
                                </span>
                            </div>

                            <div className="card-balance">
                                <div className="balance-label">Solde disponible</div>
                                <div className="balance-amount">{formattedBalance}</div>
                            </div>

                            <div className="card-bottom">
                                <div>
                                    Compte N° :{" "}
                                    <span className="card-account-id">{account.account_id}</span>
                                </div>
                                <div>Créé le : {formattedDate}</div>
                            </div>

                            <Link
                                to={`/accounts/${account.account_id}`}
                                className="card-arrow"
                            >
                                Voir le détail &rarr;
                            </Link>
                        </div>
                    );
                })}
            </div>
        </main>
    );
}
