import { useQuery } from "@tanstack/react-query";
import { Switch, Route } from "wouter";
import { useAuth } from "@/lib/auth";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { format } from "date-fns";
import { CreditCard, DollarSign, Calendar, History } from "lucide-react";

const loanApplicationSchema = z.object({
  amount: z.string().transform(Number),
  term: z.string().transform(Number),
  purpose: z.string().min(1, "Purpose is required"),
  employmentStatus: z.string().min(1, "Employment status is required"),
  monthlyIncome: z.string().transform(Number),
});

function CustomerDashboard() {
  interface Loan {
    id: string;
    status: string;
    amount: number;
    totalPaid: number;
    nextPaymentDate: string;
    payments: any[];
  }

  const { data: loans } = useQuery<Loan[]>({
    queryKey: ["/api/customer/loans"],
  });

  const activeLoan = loans?.find((loan: any) => loan.status === "active");
  const completionPercentage = activeLoan
    ? (activeLoan.totalPaid / activeLoan.amount) * 100
    : 0;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Loans</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loans?.filter((loan: any) => loan.status === "active").length || 0}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Borrowed</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${loans?.reduce((acc: number, loan: any) => acc + loan.amount, 0).toLocaleString() || 0}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Next Payment</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {activeLoan ? format(new Date(activeLoan.nextPaymentDate), "MMM d, yyyy") : "N/A"}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Payment History</CardTitle>
            <History className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {activeLoan?.payments?.length || 0} Payments
            </div>
          </CardContent>
        </Card>
      </div>

      {activeLoan && completionPercentage >= 85 && (
        <Card className="bg-primary/10">
          <CardHeader>
            <CardTitle>Refinancing Available!</CardTitle>
            <CardDescription>
              You've paid {completionPercentage.toFixed(1)}% of your current loan. 
              You may be eligible for refinancing with better terms.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="secondary">Apply for Refinancing</Button>
          </CardContent>
        </Card>
      )}

      <LoanApplication />
      <ActiveLoans loans={loans || []} />
      <PaymentHistory loans={loans || []} />
    </div>
  );
}

function LoanApplication() {
  const { toast } = useToast();
  const form = useForm<z.infer<typeof loanApplicationSchema>>({
    resolver: zodResolver(loanApplicationSchema),
    defaultValues: {
      amount: 0,
      term: 0,
      purpose: "",
      employmentStatus: "",
      monthlyIncome: 0,
    },
  });

  const onSubmit = async (values: z.infer<typeof loanApplicationSchema>) => {
    try {
      const response = await fetch("/api/customer/loans/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      });

      if (!response.ok) throw new Error();

      toast({
        title: "Success",
        description: "Loan application submitted successfully",
      });
      form.reset();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to submit loan application",
      });
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Apply for a Loan</CardTitle>
        <CardDescription>
          Fill out the form below to apply for a new loan
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="amount"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Loan Amount ($)</FormLabel>
                  <FormControl>
                    <Input type="number" min="0" step="0.01" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="term"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Term (months)</FormLabel>
                  <FormControl>
                    <Input type="number" min="1" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="purpose"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Loan Purpose</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="employmentStatus"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Employment Status</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="monthlyIncome"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Monthly Income ($)</FormLabel>
                  <FormControl>
                    <Input type="number" min="0" step="0.01" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit" className="w-full">
              Submit Application
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}

function ActiveLoans({ loans }: { loans: any[] }) {
  const activeLoans = loans?.filter(loan => loan.status === "active") || [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Active Loans</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Amount</TableHead>
              <TableHead>Term</TableHead>
              <TableHead>Interest Rate</TableHead>
              <TableHead>Next Payment</TableHead>
              <TableHead>Remaining Balance</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {activeLoans.map((loan) => (
              <TableRow key={loan.id}>
                <TableCell>${loan.amount.toLocaleString()}</TableCell>
                <TableCell>{loan.term} months</TableCell>
                <TableCell>{loan.interestRate}%</TableCell>
                <TableCell>
                  {format(new Date(loan.nextPaymentDate), "MMM d, yyyy")}
                </TableCell>
                <TableCell>
                  ${(loan.amount - loan.totalPaid).toLocaleString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function PaymentHistory({ loans }: { loans: any[] }) {
  const allPayments = loans?.flatMap(loan => 
    loan.payments.map((payment: any) => ({
      ...payment,
      loanAmount: loan.amount,
    }))
  ) || [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Payment History</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Date</TableHead>
              <TableHead>Amount</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {allPayments.map((payment) => (
              <TableRow key={payment.id}>
                <TableCell>
                  {format(new Date(payment.paymentDate), "MMM d, yyyy")}
                </TableCell>
                <TableCell>${payment.amount.toLocaleString()}</TableCell>
                <TableCell>
                  <span className={`capitalize ${
                    payment.status === "completed" ? "text-green-600" :
                    payment.status === "failed" ? "text-red-600" :
                    "text-yellow-600"
                  }`}>
                    {payment.status}
                  </span>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

export default function CustomerPortal() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!user || user.role !== "borrower") {
    return <div>Unauthorized</div>;
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="container h-16 flex items-center justify-between">
          <h1 className="text-2xl font-bold">K&R Financial Services</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">
              Welcome, {user.username}
            </span>
          </div>
        </div>
      </header>
      <main className="container py-6">
        <Switch>
          <Route path="/portal" component={CustomerDashboard} />
          <Route>404 - Not Found</Route>
        </Switch>
      </main>
    </div>
  );
}
