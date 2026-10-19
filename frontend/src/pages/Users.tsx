import { FormEvent, useEffect, useState } from "react";
import client, { errorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { NewAccountData, User, UserRole } from "../types";

const ROLES: { value: UserRole; label: string }[] = [
  { value: "CUSTOMER", label: "Customer" },
  { value: "DISTRIBUTOR", label: "Distributor" },
  { value: "ADMIN", label: "Admin" },
];

const EMPTY_ACCOUNT: NewAccountData = {
  full_name: "",
  company_name: "",
  email: "",
  password: "",
  role: "DISTRIBUTOR",
};

const ACCOUNT_FIELDS: { key: Exclude<keyof NewAccountData, "role">; label: string; type: string }[] = [
  { key: "full_name", label: "Full name", type: "text" },
  { key: "company_name", label: "Company", type: "text" },
  { key: "email", label: "Email", type: "email" },
  { key: "password", label: "Temporary password", type: "password" },
];

export default function Users() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[] | null>(null);
  const [loadError, setLoadError] = useState("");
  const [roleError, setRoleError] = useState("");
  const [savingId, setSavingId] = useState<number | null>(null);
  const [account, setAccount] = useState<NewAccountData>(EMPTY_ACCOUNT);
  const [accountError, setAccountError] = useState("");
  const [accountNotice, setAccountNotice] = useState("");
  const [creating, setCreating] = useState(false);

  const load = async () => {
    try {
      const res = await client.get<User[]>("/users");
      setUsers(res.data);
      setLoadError("");
    } catch (err) {
      setLoadError(errorMessage(err, "Couldn't load users. Refresh the page to try again."));
    }
  };

  useEffect(() => {
    load();
  }, []);

  const changeRole = async (target: User, role: UserRole) => {
    setRoleError("");
    setSavingId(target.id);
    try {
      await client.patch(`/users/${target.id}/role`, { role });
      await load();
    } catch (err) {
      setRoleError(errorMessage(err, `Couldn't change ${target.full_name}'s role. Try again.`));
    } finally {
      setSavingId(null);
    }
  };

  const createAccount = async (e: FormEvent) => {
    e.preventDefault();
    setAccountError("");
    setAccountNotice("");
    setCreating(true);
    try {
      const res = await client.post<User>("/users", account);
      setAccount(EMPTY_ACCOUNT);
      setAccountNotice(`Created ${res.data.full_name} (${res.data.role.toLowerCase()}).`);
      await load();
    } catch (err) {
      setAccountError(errorMessage(err, "Couldn't create the account. Check the details and try again."));
    } finally {
      setCreating(false);
    }
  };

  return (
    <div>
      <h1 className="text-xl font-bold text-slate-800 mb-4">Users</h1>

      <form
        onSubmit={createAccount}
        className="bg-white rounded-lg shadow-sm border border-slate-200 p-4 mb-6"
        aria-labelledby="new-account-heading"
      >
        <h2 id="new-account-heading" className="font-semibold text-slate-700 mb-1">Add an account</h2>
        <p className="text-sm text-slate-500 mb-3">
          Create distributor and admin accounts here. Customers can also sign up themselves.
        </p>
        {accountError && <p className="text-red-600 text-sm mb-3">{accountError}</p>}
        {accountNotice && <p className="text-green-700 text-sm mb-3">{accountNotice}</p>}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 items-end">
          {ACCOUNT_FIELDS.map((f) => (
            <div key={f.key}>
              <label htmlFor={`account-${f.key}`} className="block text-xs text-slate-600 mb-1">
                {f.label}
              </label>
              <input
                id={`account-${f.key}`}
                type={f.type}
                value={account[f.key] ?? ""}
                onChange={(e) => setAccount({ ...account, [f.key]: e.target.value })}
                className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"
                required={f.key !== "company_name"}
              />
            </div>
          ))}
          <div>
            <label htmlFor="account-role" className="block text-xs text-slate-600 mb-1">
              Role
            </label>
            <select
              id="account-role"
              value={account.role}
              onChange={(e) => setAccount({ ...account, role: e.target.value as UserRole })}
              className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"
            >
              {ROLES.map((r) => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </select>
          </div>
        </div>
        <button
          type="submit"
          disabled={creating}
          className="mt-4 px-4 py-2 bg-ocean-600 hover:bg-ocean-700 disabled:opacity-60 text-white rounded-md text-sm font-medium"
        >
          {creating ? "Creating…" : "Create account"}
        </button>
      </form>

      {roleError && <p className="text-red-600 text-sm mb-3">{roleError}</p>}
      {loadError && <p className="text-red-600 text-sm mb-3">{loadError}</p>}

      <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-left">
            <tr>
              <th className="px-4 py-2">Name</th>
              <th className="px-4 py-2">Email</th>
              <th className="px-4 py-2">Company</th>
              <th className="px-4 py-2">Role</th>
            </tr>
          </thead>
          <tbody>
            {users === null && !loadError && (
              <tr><td colSpan={4} className="px-4 py-6 text-slate-500">Loading users…</td></tr>
            )}
            {users?.length === 0 && (
              <tr><td colSpan={4} className="px-4 py-6 text-slate-500">No users yet.</td></tr>
            )}
            {users?.map((u) => {
              const isSelf = u.id === currentUser?.id;
              return (
                <tr key={u.id} className="border-t border-slate-100">
                  <td className="px-4 py-2 font-medium">{u.full_name}</td>
                  <td className="px-4 py-2 text-slate-500">{u.email}</td>
                  <td className="px-4 py-2">{u.company_name || "-"}</td>
                  <td className="px-4 py-2">
                    <select
                      aria-label={`Role for ${u.full_name}`}
                      value={u.role}
                      disabled={isSelf || savingId === u.id}
                      title={isSelf ? "You can't change your own role" : undefined}
                      onChange={(e) => changeRole(u, e.target.value as UserRole)}
                      className="border border-slate-300 rounded-md text-xs px-2 py-1 disabled:bg-slate-50 disabled:text-slate-500"
                    >
                      {ROLES.map((r) => (
                        <option key={r.value} value={r.value}>{r.label}</option>
                      ))}
                    </select>
                    {isSelf && <span className="ml-2 text-xs text-slate-400">(you)</span>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
