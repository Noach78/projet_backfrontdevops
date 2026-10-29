import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api.js";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const navigate = useNavigate();

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
      await api(`${apiUrl}/create_user`, {
        method: "POST",
        body: { email, password },
      });
      navigate("/login");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="register-title">
        <h1 id="register-title">Créer mon compte</h1>
        <p className="auth-description">
          Inscrivez-vous pour accéder à votre espace bancaire.
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label htmlFor="register-email">Adresse email</label>
          <input
            autoComplete="email"
            id="register-email"
            name="email"
            onChange={(event) => {
              setEmail(event.target.value);
              setError("");
            }}
            required
            type="email"
            value={email}
          />

          <label htmlFor="register-password">Mot de passe</label>
          <input
            autoComplete="new-password"
            id="register-password"
            minLength={8}
            name="password"
            onChange={(event) => {
              setPassword(event.target.value);
              setError("");
            }}
            required
            type="password"
            value={password}
          />
          <p className="password-hint">8 caractères minimum</p>

          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}

          <button disabled={isSubmitting} type="submit">
            {isSubmitting ? "Inscription en cours..." : "S'inscrire"}
          </button>
        </form>

        <p className="auth-switch">
          Déjà un compte ? <Link to="/login">Se connecter</Link>
        </p>
      </section>
    </main>
  );
}
