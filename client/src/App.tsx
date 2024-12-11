import { Switch, Route } from "wouter";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "./lib/queryClient";
import { Toaster } from "@/components/ui/toaster";
import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";
import DashboardLayout from "./components/layout/DashboardLayout";
import Home from "./pages/dashboard/Home";
import UserManagement from "./pages/dashboard/UserManagement";
import Borrowers from "./pages/dashboard/Borrowers";
import Loans from "./pages/dashboard/Loans";
import CustomerPortal from "./pages/customer/CustomerPortal";
import { useAuth } from "./lib/auth";

function App() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
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

        {/* Admin Dashboard */}
        <Route path="/dashboard/:page*">
          {user && user.role !== 'borrower' ? (
            <DashboardLayout>
              <Switch>
                <Route path="/dashboard" component={Home} />
                <Route path="/dashboard/users" component={UserManagement} />
                <Route path="/dashboard/borrowers" component={Borrowers} />
                <Route path="/dashboard/loans" component={Loans} />
                <Route>404 - Not Found</Route>
              </Switch>
            </DashboardLayout>
          ) : (
            <Login />
          )}
        </Route>

        <Route path="/">
          {user ? (
            user.role === 'borrower' ? (
              <CustomerPortal />
            ) : (
              <Home />
            )
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
