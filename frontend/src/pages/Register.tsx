import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    email: "",
    password: "",
    full_name: "",
    company_name: "",
    role: "CUSTOMER",
  });
  const [error, setError] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await register(form);
      navigate("/orders");
    } catch {
      setError("Registration failed. Email may already be in use.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-ocean-50">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded-lg shadow-md w-full max-w-sm">
        <h1 className="text-xl font-bold text-ocean-700 mb-6">Create an account</h1>
        {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

        {[
          { key: "full_name", label: "Full name", type: "text" },
          { key: "company_name", label: "Company", type: "text" },
          { key: "email", label: "Email", type: "email" },
          { key: "password", label: "Password", type: "password" },
        ].map((f) => (
          <div key={f.key} className="mb-4">
            <label className="block text-sm text-slate-600 mb-1">{f.label}</label>
            <input
              type={f.type}
              value={(form as any)[f.key]}
              onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
              className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"
              required={f.key !== "company_name"}
            />
          </div>
        ))}

        <label className="block text-sm text-slate-600 mb-1">Role</label>
        <select
          value={form.role}
          onChange={(e) => setForm({ ...form, role: e.target.value })}
          className="w-full border border-slate-300 rounded-md px-3 py-2 mb-6 text-sm"
        >
          <option value="CUSTOMER">Customer</option>
          <option value="DISTRIBUTOR">Distributor</option>
          <option value="ADMIN">Admin</option>
        </select>

        <button
          type="submit"
          className="w-full bg-ocean-600 hover:bg-ocean-700 text-white rounded-md py-2 text-sm font-medium"
        >
          Create account
        </button>
      </form>
    </div>
  );
}
