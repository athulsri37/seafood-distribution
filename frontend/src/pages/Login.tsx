import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@seafoodco.com");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await login(email, password);
      navigate("/orders");
    } catch {
      setError("Invalid email or password");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-ocean-50">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded-lg shadow-md w-full max-w-sm">
        <h1 className="text-xl font-bold text-ocean-700 mb-1">🐟 Seafood Distribution</h1>
        <p className="text-sm text-slate-500 mb-6">Sign in to your account</p>

        {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

        <label className="block text-sm text-slate-600 mb-1">Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full border border-slate-300 rounded-md px-3 py-2 mb-4 text-sm"
          required
        />

        <label className="block text-sm text-slate-600 mb-1">Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full border border-slate-300 rounded-md px-3 py-2 mb-6 text-sm"
          required
        />

        <button
          type="submit"
          className="w-full bg-ocean-600 hover:bg-ocean-700 text-white rounded-md py-2 text-sm font-medium"
        >
          Log in
        </button>

        <p className="text-xs text-slate-500 mt-4">
          No account? <Link to="/register" className="text-ocean-600 font-medium">Register</Link>
        </p>
        <p className="text-xs text-slate-400 mt-3">
          Demo: admin@seafoodco.com / Admin123!
        </p>
      </form>
    </div>
  );
}
