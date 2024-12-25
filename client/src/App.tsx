import { Switch, Route } from "wouter";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "./lib/queryClient";
import { Toaster } from "@/components/ui/toaster";
import LoadingSpinner from "./components/ui/loading-spinner";
import MainLayout from "./components/layout/MainLayout";
import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";
import Home from "./pages/dashboard/Home";
import UserManagement from "./pages/dashboard/UserManagement";
import Loans from "./pages/dashboard/Loans";
import Analytics from "./pages/dashboard/Analytics";
import CustomerPortal from "./pages/customer/CustomerPortal";
import { useAuth } from "./lib/auth";

const ProtectedRoute = ({ children, allowedRoles }: { children: React.ReactNode, allowedRoles: string[] }) => {
  const { user, isLoading } = useAuth();
  
  if (isLoading) return <LoadingSpinner />;
  if (!user || !allowedRoles.includes(user.role)) return <Login />;
  return children;
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Switch>
        <Route path="/login" component={Login} />
        <Route path="/register" component={Register} />
        
        <Route path="/portal/*">
          <ProtectedRoute allowedRoles={['borrower']}>
            <CustomerPortal />
          </ProtectedRoute>
        </Route>

        <Route path="/:page*">
          <ProtectedRoute allowedRoles={['admin', 'staff']}>
            <MainLayout>
              <Switch>
                <Route path="/" component={Home} />
                <Route path="/users" component={UserManagement} />
                <Route path="/loans" component={Loans} />
                <Route path="/analytics" component={Analytics} />
                <Route component={() => <h1 className="text-2xl font-semibold">404 - Page Not Found</h1>} />
              </Switch>
            </MainLayout>
          </ProtectedRoute>
        </Route>
      </Switch>
      <Toaster />
    </QueryClientProvider>
  );
}

export default App;
