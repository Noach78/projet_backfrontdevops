import { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { api } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function DepositPage() {
    const { accountId } = useParams();
    const { token } = useAuth();
    const navigate = useNavigate();

    const [account, setAccount] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [errorMessage, setErrorMessage] = useState("");

    const [amount, setAmount] = useState("");
    const [depositError, setDepositError] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        async function checkAccount() {
            setIsLoading(true);
            setErrorMessage("");

            try {
                const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
                const data = await api(`${apiUrl}/account_info/${accountId}`, {
                    token,
                });

                setAccount(data.account);
            } catch (err) {
                setErrorMessage(err.message || "Ce compte n'existe pas ou ne vous appartient pas.");
            } finally {
                setIsLoading(false);
            }
        }

        if (accountId) {
            checkAccount();
        }
    }, [accountId, token]);

    async function handleDeposit(e) {
        e.preventDefault();
        setDepositError("");

        const numericAmount = Number(amount);
        if (!numericAmount || numericAmount <= 0) {
            setDepositError("Le montant doit être supérieur à 0 €.");
            return;
        }
        if (numericAmount > 10000) {
            setDepositError("Le dépôt ne peut pas dépasser 10 000 €.");
            return;
        }

        setIsSubmitting(true);
        try {
            const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

            const data = await api(`${apiUrl}/credit/${accountId}/${numericAmount}`, {
                method: "POST",
                token,
            });
            setAccount((prev) => ({
                ...prev,
                sold: data.sold,
            }));
            setAmount("");
            alert("Dépôt effectué avec succès !");
            navigate(`/accounts/${accountId}`);
        } catch (err) {
            setDepositError(err.message);
        } finally {
            setIsSubmitting(false);
        }
    }


    // loading
    if (isLoading) {
        return (
            <main className="deposit-page">
                <p className="status-card" role="status">Vérification du compte en cours...</p>
            </main>
        );
    }

    // error : wrong id
    if (errorMessage) {
        return (
            <main className="deposit-page">
                <div className="error-card">
                    <h2>Compte inaccessible</h2>
                    <p>{errorMessage}</p>
                    <Link to="/">Retour au tableau de bord</Link>
                </div>
            </main>
        );
    }

    // account exist
    return (
        <main className="deposit-page">
            <h1>Déposer de l'argent</h1>
            <p>Compte n° : <strong>{accountId}</strong></p>
            {account?.sold !== undefined && <p>Solde actuel : {account.sold} €</p>}

            {depositError && <p className="status-card status-error" role="alert">{depositError}</p>}

            <form onSubmit={handleDeposit}>
                <label htmlFor="amount">Montant à déposer (€) :</label>
                <input
                    id="amount"
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    required
                />

                <button type="submit" disabled={isSubmitting}>
                    {isSubmitting ? "Dépôt en cours..." : "Valider le dépôt"}
                </button>
            </form>
        </main>
    );
}