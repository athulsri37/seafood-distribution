import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";
import client from "../api/client";
import { DashboardSummary } from "../types";
import StatCard from "../components/StatCard";

const COLORS = ["#1c6e8c", "#f59e0b", "#8b5cf6", "#10b981", "#ef4444"];

export default function Reports() {
  const [data, setData] = useState<DashboardSummary | null>(null);

  useEffect(() => {
    client.get("/reports/dashboard").then((res) => setData(res.data));
  }, []);

  if (!data) return <p className="text-slate-500">Loading reports...</p>;

  return (
    <div>
      <h1 className="text-xl font-bold text-slate-800 mb-4">Reports</h1>

      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard label="Orders (excl. cancelled)" value={data.total_orders} />
        <StatCard label="Revenue (excl. cancelled)" value={`$${data.total_revenue.toFixed(2)}`} accent="text-green-600" />
        <StatCard label="Customers" value={data.total_customers} />
        <StatCard label="Low Stock Items" value={data.low_stock_count} accent="text-red-600" />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
          <h2 className="font-semibold text-slate-700 mb-3">Orders by Status</h2>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={data.sales_by_status}
                dataKey="order_count"
                nameKey="status"
                cx="50%"
                cy="50%"
                outerRadius={90}
                label
              >
                {data.sales_by_status.map((_, idx) => (
                  <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
          <h2 className="font-semibold text-slate-700 mb-3">Top Products by Units Sold (excl. cancelled)</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data.top_products}>
              <XAxis dataKey="product_name" tick={{ fontSize: 11 }} interval={0} angle={-15} textAnchor="end" height={60} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="units_sold" fill="#1c6e8c" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
