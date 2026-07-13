import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-2 rounded-md text-sm font-medium ${
      isActive ? "bg-ocean-600 text-white" : "text-ocean-700 hover:bg-ocean-100"
    }`;

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-6">
          <span className="text-lg font-bold text-ocean-700">🐟 Seafood Distribution</span>
          <div className="flex gap-1">
            <NavLink to="/orders" className={linkClass}>Orders</NavLink>
            <NavLink to="/inventory" className={linkClass}>Inventory</NavLink>
            {(user?.role === "ADMIN" || user?.role === "DISTRIBUTOR") && (
              <>
                <NavLink to="/reports" className={linkClass}>Reports</NavLink>
              </>
            )}
            {user?.role === "ADMIN" && (
              <NavLink to="/users" className={linkClass}>Users</NavLink>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <span className="text-slate-600">
            {user?.full_name} <span className="text-slate-400">({user?.role})</span>
          </span>
          <button
            onClick={handleLogout}
            className="px-3 py-1.5 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700"
          >
            Log out
          </button>
        </div>
      </nav>
      <main className="p-6 max-w-7xl mx-auto">
        <Outlet />
      </main>
    </div>
  );
}
