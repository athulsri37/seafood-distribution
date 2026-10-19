import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { errorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { RegisterData } from "../types";

type RegisterForm = Required<RegisterData>;

const FIELDS: { key: keyof RegisterForm; label: string; type: string }[] = [
  { key: "full_name", label: "Full name", type: "text" },
  { key: "company_name", label: "Company", type: "text" },
  { key: "email", label: "Email", type: "email" },
  { key: "password", label: "Password", type: "password" },
];

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState<RegisterForm>({
    email: "",
    password: "",
    full_name: "",
    company_name: "",
  });
  const [error, setError] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await register(form);
      navigate("/orders");
    } catch (err) {
      setError(errorMessage(err, "Registration failed. Check your details and try again."));
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-ocean-50">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded-lg shadow-md w-full max-w-sm">
        <h1 className="text-xl font-bold text-ocean-700 mb-1">Create a customer account</h1>
        <p className="text-sm text-slate-500 mb-6">
          Distributor and admin accounts are set up by an admin.
        </p>
        {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

        {FIELDS.map((f) => (
          <div key={f.key} className="mb-4">
            <label htmlFor={`register-${f.key}`} className="block text-sm text-slate-600 mb-1">
              {f.label}
            </label>
            <input
              id={`register-${f.key}`}
              type={f.type}
              value={form[f.key]}
              onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
              className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"
              required={f.key !== "company_name"}
            />
          </div>
        ))}

        <button
          type="submit"
          className="w-full bg-ocean-600 hover:bg-ocean-700 text-white rounded-md py-2 mt-2 text-sm font-medium"
        >
          Create account
        </button>

        <p className="text-xs text-slate-500 mt-4">
          Already have an account? <Link to="/login" className="text-ocean-600 font-medium">Log in</Link>
        </p>
      </form>
    </div>
  );
}
