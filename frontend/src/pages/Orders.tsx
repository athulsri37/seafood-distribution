import { useEffect, useState } from "react";
import client, { errorMessage } from "../api/client";
import { Order, OrderStatus, Product } from "../types";
import { useAuth } from "../context/AuthContext";

const STATUS_COLORS: Record<OrderStatus, string> = {
  PENDING: "bg-amber-100 text-amber-700",
  CONFIRMED: "bg-blue-100 text-blue-700",
  IN_TRANSIT: "bg-purple-100 text-purple-700",
  DELIVERED: "bg-green-100 text-green-700",
  CANCELLED: "bg-red-100 text-red-700",
};

export default function Orders() {
  const { user } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [showNewOrder, setShowNewOrder] = useState(false);
  const [cart, setCart] = useState<Record<number, number>>({});
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const canManage = user?.role === "ADMIN" || user?.role === "DISTRIBUTOR";

  const loadOrders = async () => {
    const res = await client.get("/orders");
    setOrders(res.data);
  };

  const loadProducts = async () => {
    const res = await client.get("/products");
    setProducts(res.data);
  };

  useEffect(() => {
    loadOrders();
    loadProducts();
  }, []);

  const submitOrder = async () => {
    const items = Object.entries(cart)
      .filter(([, qty]) => qty > 0)
      .map(([product_id, quantity]) => ({ product_id: Number(product_id), quantity }));
    if (items.length === 0) return;
    setError("");
    setSubmitting(true);
    try {
      await client.post("/orders", { items });
      setCart({});
      setShowNewOrder(false);
      loadOrders();
    } catch (err) {
      // Usually another customer bought the last units first; the refreshed stock shows what's left.
      setError(errorMessage(err, "Couldn't place the order. Try again."));
    } finally {
      setSubmitting(false);
      loadProducts();
    }
  };

  const updateStatus = async (orderId: number, status: OrderStatus) => {
    setError("");
    try {
      await client.patch(`/orders/${orderId}/status`, { status });
    } catch (err) {
      setError(errorMessage(err, `Couldn't update order #${orderId}. Try again.`));
    }
    loadOrders();
    loadProducts();
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-slate-800">Orders</h1>
        <button
          onClick={() => setShowNewOrder(!showNewOrder)}
          className="px-3 py-1.5 bg-ocean-600 hover:bg-ocean-700 text-white rounded-md text-sm"
        >
          {showNewOrder ? "Cancel" : "+ New Order"}
        </button>
      </div>

      {error && (
        <p role="alert" className="mb-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      {showNewOrder && (
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4 mb-6">
          <h2 className="font-semibold text-slate-700 mb-3">Create Order</h2>
          <div className="grid grid-cols-2 gap-3 mb-4">
            {products.map((p) => (
              <div key={p.id} className="flex items-center justify-between border border-slate-100 rounded-md p-2">
                <div>
                  <p className="text-sm font-medium">{p.name}</p>
                  <p className="text-xs text-slate-500">${p.price_per_unit.toFixed(2)} / {p.unit} · {p.quantity_on_hand} in stock</p>
                </div>
                <input
                  type="number"
                  aria-label={`Quantity of ${p.name}`}
                  min={0}
                  max={p.quantity_on_hand}
                  value={cart[p.id] || ""}
                  onChange={(e) =>
                    setCart({ ...cart, [p.id]: parseInt(e.target.value || "0", 10) })
                  }
                  className="w-16 border border-slate-300 rounded-md px-2 py-1 text-sm"
                />
              </div>
            ))}
          </div>
          <button
            onClick={submitOrder}
            disabled={submitting}
            className="px-4 py-2 bg-ocean-600 hover:bg-ocean-700 disabled:opacity-60 text-white rounded-md text-sm font-medium"
          >
            {submitting ? "Placing order…" : "Submit Order"}
          </button>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-left">
            <tr>
              <th className="px-4 py-2">Order #</th>
              <th className="px-4 py-2">Customer</th>
              <th className="px-4 py-2">Items</th>
              <th className="px-4 py-2">Total</th>
              <th className="px-4 py-2">Status</th>
              {canManage && <th className="px-4 py-2">Update</th>}
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.id} className="border-t border-slate-100">
                <td className="px-4 py-2 font-medium">#{o.id}</td>
                <td className="px-4 py-2">{o.customer.full_name}</td>
                <td className="px-4 py-2 text-slate-500">
                  {o.items.map((i) => `${i.product_name} x${i.quantity}`).join(", ")}
                </td>
                <td className="px-4 py-2">${o.total_amount.toFixed(2)}</td>
                <td className="px-4 py-2">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[o.status]}`}>
                    {o.status}
                  </span>
                </td>
                {canManage && (
                  <td className="px-4 py-2">
                    <select
                      value={o.status}
                      onChange={(e) => updateStatus(o.id, e.target.value as OrderStatus)}
                      className="border border-slate-300 rounded-md text-xs px-2 py-1"
                    >
                      {["PENDING", "CONFIRMED", "IN_TRANSIT", "DELIVERED", "CANCELLED"].map((s) => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </select>
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
