import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";

const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function getUserIdFromToken(token) {
    try {
        const payload = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
        return window.atob(payload).match(/"user_id"\s*:\s*(\d+)/)?.[1] ?? null;
    } catch {
        return null;
    }
}

export default function CreateAccount() {
    const [response, setResponse] = useState(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    async function handleSubmit(event) {
        event.preventDefault();

        const token = localStorage.getItem("token");
        const userId = token ? getUserIdFromToken(token) : null;
        if (!userId) {
            setResponse({
                type: "error",
                message: "Votre session a expiré. Veuillez vous reconnecter.",
            });
            return;
        }

        setResponse(null);
        setIsSubmitting(true);
        try {
            const data = await api(`${apiUrl}/create_account/${userId}`, {
                method: "POST",
                token,
            });
            setResponse({
                type: "success",
                message: `${data.message} (Compte n° ${data.account_id})`,
            });
        } catch (error) {
            setResponse({ type: "error", error: error.message });
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <main>
            <form onSubmit={handleSubmit}>
                <h1>Créer un compte</h1>
                <p>Le type du compte est attribué automatiquement.</p>
                <button type="submit" disabled={isSubmitting}>
                    {isSubmitting ? "Création en cours…" : "Ouvrir un compte"}
                </button>
            </form>
            {response && (
                <p role={response.type === "error" ? "alert" : "status"}>
                    {response.message}
                </p>
            )}
            <Link to="/dashboard">Retour au tableau de bord</Link>
        </main>
    );
}
