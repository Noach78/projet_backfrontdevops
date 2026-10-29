import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";

const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export default function CloseAccount({ accountId, accountType }) {
    const { token } = useAuth();
    const navigate = useNavigate();
    const [errorMessage, setErrorMessage] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    async function handleCloseAccount() {
        if (!window.confirm("Voulez-vous vraiment clôturer ce compte ?")) {
            return;
        }

        setErrorMessage("");
        setIsSubmitting(true);

        try {
            await api(`${apiUrl}/close_account/${accountId}`, {
                method: "POST",
                token,
            });
            navigate("/accounts");
        } catch (error) {
            setErrorMessage(error.message || "La clôture du compte a échoué.");
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <div>
            {accountType === "principal" ? (
                <p role="status">Le compte principal ne peut pas être clôturé.</p>
            ) : (
                <button
                    type="button"
                    className="btn-secondary"
                    onClick={handleCloseAccount}
                    disabled={isSubmitting}
                >
                    {isSubmitting ? "Clôture en cours…" : "Clôturer ce compte"}
                </button>
            )}
            {errorMessage && <p role="alert">{errorMessage}</p>}
        </div>
    );
}
