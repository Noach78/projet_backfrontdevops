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
    const [response, setResponse] = useState(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [form, setForm] = useState({
        name: "",
        account_id: "",
    });

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

    function handleChange(event) {
        const { name, value } = event.target;
        setForm((prev) => ({ ...prev, [name]: value }));
    }

    async function handleSubmit(event) {
        event.preventDefault();
        const ownerId = token ? getUserIdFromToken(token) : null;
        if (!ownerId) {
            setResponse({ type: "error", message: "Session invalide. Veuillez vous reconnecter." });
            return;
        }

        const body = {
            owner_id: ownerId,
            name: form.name,
            account_id: form.account_id,
        };

        setResponse(null);
        setIsSubmitting(true);

        try {
            const result = await api(`${apiUrl}/add_beneficiary`, {
                method: "POST",
                body,
                token,
            });

            setResponse({ type: "success", message: result.message });
            setForm({ name: "", account_id: "" });

            const data = await api(`${apiUrl}/beneficiaries/${ownerId}`, { token });
            setBeneficiaries(data.beneficiaries ?? []);
        } catch (error) {
            setResponse({ type: "error", message: error.message });
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <section className="beneficiaries-page">
            <header>
                <h1>Mes bénéficiaires</h1>
            </header>

            <form className="add-beneficiary-form" onSubmit={handleSubmit}>
                <input
                    name="name"
                    type="text"
                    placeholder="Nom du bénéficiaire"
                    value={form.name}
                    onChange={handleChange}
                    required
                />
                <input
                    name="account_id"
                    type="text"
                    placeholder="Numéro de compte"
                    value={form.account_id}
                    onChange={handleChange}
                    required
                />
                <button type="submit" disabled={isSubmitting}>
                    {isSubmitting ? "Ajout en cours…" : "Ajouter"}
                </button>
            </form>

            {response && (
                <p role={response.type === "error" ? "alert" : "status"}>
                    {response.message}
                </p>
            )}

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
