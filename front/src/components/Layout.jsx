import { Outlet, NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function Layout() {
  const { token, logout } = useAuth();

  return (
    <>
      <header className="app-header">
        <nav className="app-nav">
          <NavLink to="/" end>
            Accueil
          </NavLink>

          {token ? (
            <>
              <button className="btn-logout" onClick={logout} type="button">
                Déconnexion
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login">Connexion</NavLink>
              <NavLink to="/register">Inscription</NavLink>
              <NavLink to="/deposit">Depot</NavLink>
            </>
          )}
        </nav>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </>
  );
}
