import { useState } from "react";
import { Link, useNavigate, Navigate } from "react-router-dom";
import { api } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function LoginPage() {
  const { token, login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const navigate = useNavigate();

  if (token) {
    return <Navigate to="/" replace />;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
      const data = await api(`${apiUrl}/login_user`, {
        method: "POST",
        body: { email, password },
      });
      login(data.accessToken ?? data.token);
      navigate("/", { replace: true });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="login-title">
        <h1 id="login-title">Connexion</h1>
        <p className="auth-description">
          Connectez-vous pour accéder à votre espace bancaire.
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label htmlFor="login-email">Adresse email</label>
          <input
            autoComplete="email"
            id="login-email"
            name="email"
            onChange={(event) => {
              setEmail(event.target.value);
              setError("");
            }}
            required
            type="email"
            value={email}
          />

          <label htmlFor="login-password">Mot de passe</label>
          <input
            autoComplete="current-password"
            id="login-password"
            name="password"
            onChange={(event) => {
              setPassword(event.target.value);
              setError("");
            }}
            required
            type="password"
            value={password}
          />

          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}

          <button disabled={isSubmitting} type="submit">
            {isSubmitting ? "Connexion en cours..." : "Se connecter"}
          </button>
        </form>

        <p className="auth-switch">
          Pas encore de compte ? <Link to="/register">S'inscrire</Link>
        </p>
      </section>
    </main>
  );
}