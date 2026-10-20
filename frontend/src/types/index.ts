export type UserRole = "ADMIN" | "DISTRIBUTOR" | "CUSTOMER";

export interface User {
  id: number;
  email: string;
  full_name: string;
  company_name?: string | null;
  role: UserRole;
  created_at: string;
}

/** Self-registration always creates a customer account. */
export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  company_name?: string;
}

/** An admin creating an account with any role. */
export interface NewAccountData extends RegisterData {
  role: UserRole;
}

export interface Product {
  id: number;
  name: string;
  species: string;
  sku: string;
  unit: string;
  price_per_unit: number;
  quantity_on_hand: number;
  reorder_threshold: number;
  warehouse_location?: string | null;
  is_low_stock: boolean;
  created_at: string;
}

export type OrderStatus =
  | "PENDING"
  | "CONFIRMED"
  | "IN_TRANSIT"
  | "DELIVERED"
  | "CANCELLED";

export interface OrderItem {
  id: number;
  product_id: number;
  product_name: string;
  quantity: number;
  unit_price: number;
}

export interface Order {
  id: number;
  status: OrderStatus;
  /** Statuses the order may move to next; empty once it's delivered or cancelled. */
  next_statuses: OrderStatus[];
  total_amount: number;
  customer: User;
  items: OrderItem[];
  created_at: string;
}

export interface DashboardSummary {
  total_orders: number;
  total_revenue: number;
  total_customers: number;
  low_stock_count: number;
  sales_by_status: { status: string; order_count: number; total_revenue: number }[];
  top_products: { product_name: string; units_sold: number; revenue: number }[];
}
