import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import HomePage from "./pages/HomePage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import RegisterPage from "./pages/RegisterPage.jsx";
import TransferPage from "./pages/TransferPage.jsx";
import DepositPage from "./pages/DepositPage.jsx";
import HistoryPage from "./pages/HistoryPage.jsx";
import Account from "./pages/AccountPage.jsx";
import AllAccountsPage from "./pages/AllAccountsPage.jsx";
import CreateAccountPage from "./pages/CreateAccountPage.jsx";
import BeneficiaryPage from "./pages/BeneficiaryPage.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route element={<Layout />}>
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/dashboard" element={<HomePage />} />
          <Route
            path="/accounts/:accountId/history"
            element={<HistoryPage />}
          />
          <Route path="/transfer" element={<TransferPage />} />
          <Route path="/deposit/:accountId" element={<DepositPage />} />
          <Route path="/accounts/:accountId" element={<Account />} />
          <Route path="/accounts" element={<AllAccountsPage />} />
          <Route path="/accounts/new" element={<CreateAccountPage />} />
          <Route path="/beneficiaries" element={<BeneficiaryPage />} />
        </Route>
      </Route>

      <Route path="*" element={<main className="not-found-page"><h1>Page introuvable</h1><p>Cette page n’existe pas ou a été déplacée.</p></main>} />
    </Routes>
  );
}
