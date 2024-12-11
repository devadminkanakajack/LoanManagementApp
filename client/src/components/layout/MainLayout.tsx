import React from "react";
import { Link, useLocation } from "wouter";
import { 
  LayoutGrid, 
  Users, 
  FileText, 
  PieChart, 
  Settings, 
  HelpCircle,
  Menu
} from "lucide-react";

const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [location] = useLocation();
  const [sidebarOpen, setSidebarOpen] = React.useState(true);

  const menuItems = [
    { icon: LayoutGrid, label: "Dashboard", path: "/" },
    { icon: Users, label: "User Management", path: "/users" },
    { icon: FileText, label: "Loan Applications", path: "/loans" },
    { icon: PieChart, label: "Analytics", path: "/analytics" },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Top Navigation */}
      <header className="fixed top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex h-14 items-center px-4 gap-4">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="lg:hidden"
          >
            <Menu className="h-6 w-6" />
          </button>
          <div className="flex-1" />
          <nav className="flex items-center gap-4">
            <Link href="/settings">
              <Settings className="h-5 w-5 cursor-pointer" />
            </Link>
            <Link href="/help">
              <HelpCircle className="h-5 w-5 cursor-pointer" />
            </Link>
          </nav>
        </div>
      </header>

      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-14 z-40 h-[calc(100vh-3.5rem)] w-64 border-r bg-background transition-transform lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <nav className="space-y-2 p-4">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = location === item.path;
            return (
              <Link key={item.path} href={item.path}>
                <a
                  className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground ${
                    isActive ? "bg-accent" : ""
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  {item.label}
                </a>
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <main className={`pt-14 transition-all ${sidebarOpen ? "lg:pl-64" : ""}`}>
        <div className="container mx-auto p-4 lg:p-8">{children}</div>
      </main>
    </div>
  );
};

export default MainLayout;
