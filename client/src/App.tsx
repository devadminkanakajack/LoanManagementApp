import { Switch, Route } from "wouter";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "./lib/queryClient";
import { Toaster } from "@/components/ui/toaster";
import MainLayout from "./components/layout/MainLayout";
import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";
import Home from "./pages/dashboard/Home";
import UserManagement from "./pages/dashboard/UserManagement";
import Loans from "./pages/dashboard/Loans";
import Analytics from "./pages/dashboard/Analytics";
import CustomerPortal from "./pages/customer/CustomerPortal";
import { useAuth } from "./lib/auth";

function App() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <Switch>
        <Route path="/login" component={Login} />
        <Route path="/register" component={Register} />
        
        {/* Customer Portal */}
        <Route path="/portal/*">
          {user?.role === 'borrower' ? <CustomerPortal /> : <Login />}
        </Route>

        {/* Admin and Staff Dashboard */}
        <Route path="/:page*">
          {user && user.role !== 'borrower' ? (
            <MainLayout>
              <Switch>
                <Route path="/" component={Home} />
                <Route path="/users" component={UserManagement} />
                <Route path="/loans" component={Loans} />
                <Route path="/analytics" component={Analytics} />
                <Route>
                  <div className="flex h-[80vh] items-center justify-center">
                    <h1 className="text-2xl font-semibold">404 - Page Not Found</h1>
                  </div>
                </Route>
              </Switch>
            </MainLayout>
          ) : (
            <Login />
          )}
        </Route>
      </Switch>
      <Toaster />
    </QueryClientProvider>
  );
}

export default App;
