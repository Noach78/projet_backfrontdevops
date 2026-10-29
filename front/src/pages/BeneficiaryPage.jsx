import { useState, useEffect } from "react";
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

export default function BeneficiaryPage() {
    const { token } = useAuth();
    const userId = token ? getUserIdFromToken(token) : null;
    const [beneficiaries, setBeneficiaries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        if (!userId) {
            return;
        }

        const controller = new AbortController();

        async function loadBeneficiaries() {
            try {
                setLoading(true);
                setError("");
                const data = await api(`${apiUrl}/beneficiaries/${userId}`, {
                    token,
                });
                setBeneficiaries(data.beneficiaries ?? []);
            } catch (err) {
                if (err.name !== "AbortError") {
                    setError(err.message || "Impossible de récupérer les bénéficiaires.");
                }
            } finally {

                setLoading(false);
            }
        }

        loadBeneficiaries();

        return () => controller.abort();
    }, [token, userId]);

    return (
        <section className="beneficiaries-page">
            <header>
                <h1>Mes bénéficiaires</h1>
            </header>

            {!userId ? (
                <p role="alert" className="form-error">Session invalide. Veuillez vous reconnecter.</p>
            ) : loading ? (
                <p role="status">Chargement de vos bénéficiaires…</p>
            ) : error ? (
                <p role="alert" className="form-error">{error}</p>
            ) : beneficiaries.length === 0 ? (
                <div className="empty-state">
                    <p>Vous n'avez encore aucun bénéficiaire enregistré.</p>
                </div>
            ) : (
                <ul className="beneficiaries-list">
                    {beneficiaries.map((beneficiary) => (
                        <li key={beneficiary.id} className="beneficiary-item">
                            <article>
                                <h2>{beneficiary.name}</h2>
                                <p>
                                    Compte N° : <strong>{beneficiary.account_id}</strong>
                                </p>
                                {beneficiary.added_at && (
                                    <p>
                                        Ajouté le :{" "}
                                        {new Date(beneficiary.added_at).toLocaleDateString("fr-FR")}
                                    </p>
                                )}
                            </article>
                        </li>
                    ))}
                </ul>
            )}
        </section>
    );
}
