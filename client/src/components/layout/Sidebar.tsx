import { Link, useLocation } from "wouter";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth";
import {
  Users,
  UserCircle,
  CreditCard,
  PiggyBank,
  BarChart3,
  Calculator,
  ScrollText,
  Settings,
} from "lucide-react";

const menuItems = [
  { icon: BarChart3, label: "Dashboard", path: "/dashboard", roles: ["super_admin", "administrator", "sales_officer", "accounts_officer", "recoveries_officer", "office_admin"] },
  { icon: Users, label: "User Management", path: "/dashboard/users", roles: ["super_admin", "administrator"] },
  { icon: UserCircle, label: "Borrowers", path: "/dashboard/borrowers", roles: ["super_admin", "administrator", "sales_officer", "accounts_officer", "recoveries_officer"] },
  { icon: CreditCard, label: "Loans", path: "/dashboard/loans", roles: ["super_admin", "administrator", "sales_officer", "accounts_officer"] },
  { icon: PiggyBank, label: "Collections", path: "/dashboard/collections", roles: ["super_admin", "administrator", "accounts_officer"] },
  { icon: ScrollText, label: "Reports", path: "/dashboard/reports", roles: ["super_admin", "administrator", "accounts_officer", "office_admin"] },
  { icon: Calculator, label: "Accounting", path: "/dashboard/accounting", roles: ["super_admin", "administrator", "accounts_officer"] },
];

export default function Sidebar() {
  const [location] = useLocation();
  const { user } = useAuth();

  const filteredMenuItems = menuItems.filter(item => 
    item.roles.includes(user?.role || '')
  );

  return (
    <div className="w-64 bg-sidebar border-r border-sidebar-border">
      <div className="p-6">
        <h2 className="text-xl font-bold text-sidebar-foreground">K&R Financial</h2>
      </div>
      
      <nav className="space-y-1 px-3">
        {filteredMenuItems.map((item) => {
          const Icon = item.icon;
          const isActive = location === item.path;
          
          return (
            <Link
              key={item.path}
              href={item.path}
              className={cn(
                "flex items-center px-3 py-2 text-sm font-medium rounded-md",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground hover:bg-sidebar-accent/50"
              )}
            >
              <Icon className="h-5 w-5 mr-2" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
