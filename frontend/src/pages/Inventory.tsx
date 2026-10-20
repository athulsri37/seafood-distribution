import { useEffect, useState } from "react";
import client, { errorMessage } from "../api/client";
import { Product } from "../types";
import { useAuth } from "../context/AuthContext";

export default function Inventory() {
  const { user } = useAuth();
  const [products, setProducts] = useState<Product[]>([]);
  const [lowStockOnly, setLowStockOnly] = useState(false);
  const [error, setError] = useState("");
  const [savingId, setSavingId] = useState<number | null>(null);
  const canManage = user?.role === "ADMIN" || user?.role === "DISTRIBUTOR";

  const load = async () => {
    const res = await client.get("/products", { params: { low_stock_only: lowStockOnly } });
    setProducts(res.data);
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lowStockOnly]);

  // Send the change, not a new total, so two people adjusting at once both count.
  const adjustStock = async (id: number, change: number) => {
    setError("");
    setSavingId(id);
    try {
      await client.post(`/products/${id}/stock-adjustments`, { change });
    } catch (err) {
      setError(errorMessage(err, "Couldn't update the stock. Try again."));
    } finally {
      setSavingId(null);
      load();
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-slate-800">Inventory</h1>
        <label className="flex items-center gap-2 text-sm text-slate-600">
          <input
            type="checkbox"
            checked={lowStockOnly}
            onChange={(e) => setLowStockOnly(e.target.checked)}
          />
          Low stock only
        </label>
      </div>

      {error && (
        <p role="alert" className="mb-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-left">
            <tr>
              <th className="px-4 py-2">Product</th>
              <th className="px-4 py-2">SKU</th>
              <th className="px-4 py-2">Species</th>
              <th className="px-4 py-2">Price / {"{unit}"}</th>
              <th className="px-4 py-2">Stock</th>
              <th className="px-4 py-2">Location</th>
              {canManage && <th className="px-4 py-2">Adjust</th>}
            </tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.id} className="border-t border-slate-100">
                <td className="px-4 py-2 font-medium text-slate-800">{p.name}</td>
                <td className="px-4 py-2 text-slate-500">{p.sku}</td>
                <td className="px-4 py-2">{p.species}</td>
                <td className="px-4 py-2">${p.price_per_unit.toFixed(2)} / {p.unit}</td>
                <td className="px-4 py-2">
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      p.is_low_stock ? "bg-red-100 text-red-700" : "bg-green-100 text-green-700"
                    }`}
                  >
                    {p.quantity_on_hand} {p.unit}
                    {p.is_low_stock ? " · Low" : ""}
                  </span>
                </td>
                <td className="px-4 py-2 text-slate-500">{p.warehouse_location || "-"}</td>
                {canManage && (
                  <td className="px-4 py-2 flex gap-2">
                    <button
                      onClick={() => adjustStock(p.id, -10)}
                      disabled={savingId === p.id || p.quantity_on_hand < 10}
                      aria-label={`Remove 10 ${p.unit} of ${p.name}`}
                      title={p.quantity_on_hand < 10 ? `Only ${p.quantity_on_hand} ${p.unit} in stock` : undefined}
                      className="px-2 py-1 bg-slate-100 hover:bg-slate-200 disabled:opacity-50 rounded text-xs"
                    >
                      -10
                    </button>
                    <button
                      onClick={() => adjustStock(p.id, 10)}
                      disabled={savingId === p.id}
                      aria-label={`Add 10 ${p.unit} of ${p.name}`}
                      className="px-2 py-1 bg-slate-100 hover:bg-slate-200 disabled:opacity-50 rounded text-xs"
                    >
                      +10
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
