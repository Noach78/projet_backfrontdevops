import { useEffect, useState } from "react";
import { api } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";

const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function getUserIdFromToken(token) {
  try {
    const payload = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    const decodedPayload = window.atob(payload);
    return decodedPayload.match(/"user_id"\s*:\s*(\d+)/)?.[1] ?? null;
  } catch {
    return null;
  }
}

export default function TransferPage() {
  const { token } = useAuth();
  const [accounts, setAccounts] = useState([]);
  const [beneficiaries, setBeneficiaries] = useState([]);
  const [sourceAccountId, setSourceAccountId] = useState("");
  const [recipientAccountId, setRecipientAccountId] = useState("");
  const [amount, setAmount] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadData() {
      const userId = token ? getUserIdFromToken(token) : null;
      try {
        const [accountsData, beneficiariesData] = await Promise.all([
          api(`${apiUrl}/my_accounts`, { token }),
          userId
            ? api(`${apiUrl}/beneficiaries/${userId}`, { token })
            : Promise.resolve({ beneficiaries: [] }),
        ]);
        if (active) {
          setAccounts(accountsData.accounts || []);
          setBeneficiaries(beneficiariesData.beneficiaries || []);
        }
      } catch (requestError) {
        if (active) setError(requestError.message);
      } finally {
        if (active) setIsLoading(false);
      }
    }

    loadData();
    return () => {
      active = false;
    };
  }, [token]);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSuccess("");
    setIsSubmitting(true);

    let transferCompleted = false;
    try {
      await api(
        `${apiUrl}/transaction/${sourceAccountId}/${recipientAccountId}/${amount}`,
        { method: "POST", token },
      );
      transferCompleted = true;

      const data = await api(`${apiUrl}/my_accounts`, { token });
      setAccounts(data.accounts);
      setSuccess("Virement effectué. Le solde a été actualisé.");
      setSourceAccountId("");
      setRecipientAccountId("");
      setAmount("");
    } catch (requestError) {
      setError(
        transferCompleted
          ? `Virement effectué, mais les soldes n'ont pas pu être actualisés : ${requestError.message}`
          : requestError.message,
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="transfer-card" aria-labelledby="transfer-title">
      <h1 id="transfer-title">Effectuer un virement</h1>
      <p className="transfer-description">
        Choisissez un compte à débiter et indiquez le numéro du compte destinataire.
      </p>

      {isLoading ? (
        <p>Chargement de vos comptes...</p>
      ) : (
        <form className="transfer-form" onSubmit={handleSubmit}>
          <label htmlFor="source-account">Compte source</label>
          <select
            id="source-account"
            onChange={(event) => setSourceAccountId(event.target.value)}
            required
            value={sourceAccountId}
          >
            <option value="" disabled>Choisir un compte</option>
            {accounts.map((account) => (
              <option key={account.account_id} value={account.account_id}>
                Compte {account.account_id} —{" "}
                {new Intl.NumberFormat("fr-FR", {
                  style: "currency",
                  currency: "EUR",
                }).format(account.sold)}
              </option>
            ))}
          </select>

          <label htmlFor="beneficiary-select">Choisir un bénéficiaire</label>
          <select
            id="beneficiary-select"
            onChange={(event) => setRecipientAccountId(event.target.value)}
            value={
              beneficiaries.some(
                (b) => String(b.account_id) === String(recipientAccountId),
              )
                ? recipientAccountId
                : ""
            }
          >
            <option value="">
              {beneficiaries.length === 0
                ? "Aucun bénéficiaire enregistré"
                : "Sélectionner un bénéficiaire"}
            </option>
            {beneficiaries.map((beneficiary) => (
              <option key={beneficiary.id} value={beneficiary.account_id}>
                {beneficiary.name} — Compte {beneficiary.account_id}
              </option>
            ))}
          </select>

          <label htmlFor="recipient-account">Numéro du compte destinataire</label>
          <input
            autoComplete="off"
            id="recipient-account"
            inputMode="numeric"
            onChange={(event) => setRecipientAccountId(event.target.value)}
            pattern="[0-9]+"
            placeholder="Ex : 12345678"
            required
            type="text"
            value={recipientAccountId}
          />

          <label htmlFor="transfer-amount">Montant (€)</label>
          <input
            id="transfer-amount"
            min="1"
            onChange={(event) => setAmount(event.target.value)}
            required
            step="1"
            type="number"
            value={amount}
          />

          {accounts.length === 0 && (
            <p className="transfer-error" role="alert">
              Aucun compte actif n'est associé à votre session.
            </p>
          )}
          {error && (
            <p className="transfer-error" role="alert">
              {error}
            </p>
          )}
          {success && (
            <p className="transfer-success" role="status">
              {success}
            </p>
          )}

          <button
            disabled={isSubmitting || accounts.length === 0}
            type="submit"
          >
            {isSubmitting ? "Virement en cours..." : "Envoyer le virement"}
          </button>
        </form>
      )}
    </section>
  );
}
