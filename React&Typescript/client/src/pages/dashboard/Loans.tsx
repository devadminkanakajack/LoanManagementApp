import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
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
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { format } from "date-fns";

export default function Loans() {
  const { toast } = useToast();
  const [isAddingLoan, setIsAddingLoan] = useState(false);

  const { data: loans, isLoading } = useQuery({
    queryKey: ["/api/loans"],
  });

  const handleAddLoan = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    
    try {
      const response = await fetch("/api/loans", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          borrowerId: formData.get("borrowerId"),
          amount: Number(formData.get("amount")),
          term: Number(formData.get("term")),
          interestRate: Number(formData.get("interestRate")),
          purpose: formData.get("purpose"),
        }),
      });

      if (!response.ok) throw new Error();

      toast({
        title: "Success",
        description: "Loan added successfully",
      });
      setIsAddingLoan(false);
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to add loan",
      });
    }
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Loans</h1>
        <Dialog open={isAddingLoan} onOpenChange={setIsAddingLoan}>
          <DialogTrigger asChild>
            <Button>New Loan</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Loan</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleAddLoan} className="space-y-4">
              <div className="space-y-2">
                <label>Amount</label>
                <Input
                  name="amount"
                  type="number"
                  min="0"
                  step="0.01"
                  required
                />
              </div>
              <div className="space-y-2">
                <label>Term (months)</label>
                <Input
                  name="term"
                  type="number"
                  min="1"
                  required
                />
              </div>
              <div className="space-y-2">
                <label>Interest Rate (%)</label>
                <Input
                  name="interestRate"
                  type="number"
                  min="0"
                  step="0.01"
                  required
                />
              </div>
              <div className="space-y-2">
                <label>Purpose</label>
                <Input name="purpose" required />
              </div>
              <Button type="submit" className="w-full">
                Create Loan
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Borrower</TableHead>
            <TableHead>Amount</TableHead>
            <TableHead>Term</TableHead>
            <TableHead>Interest Rate</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Created At</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {loans?.map((loan: any) => (
            <TableRow key={loan.id}>
              <TableCell>
                {loan.borrower.fullName}
              </TableCell>
              <TableCell>
                ${loan.amount.toLocaleString()}
              </TableCell>
              <TableCell>{loan.term} months</TableCell>
              <TableCell>{loan.interestRate}%</TableCell>
              <TableCell>
                <span className={`capitalize ${
                  loan.status === "active" ? "text-green-600" :
                  loan.status === "defaulted" ? "text-red-600" :
                  "text-yellow-600"
                }`}>
                  {loan.status}
                </span>
              </TableCell>
              <TableCell>
                {format(new Date(loan.createdAt), "MMM d, yyyy")}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
