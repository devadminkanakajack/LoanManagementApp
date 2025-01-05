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
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import { Upload } from "lucide-react";

export default function Borrowers() {
  const { toast } = useToast();
  const [fileInput, setFileInput] = useState<HTMLInputElement | null>(null);

  const { data: borrowers, isLoading } = useQuery({
    queryKey: ["/api/borrowers"],
  });

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("/api/borrowers/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error();

      toast({
        title: "Success",
        description: "Borrowers imported successfully",
      });
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to import borrowers",
      });
    }
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Borrowers</h1>
        <div className="flex items-center gap-4">
          <Input
            type="file"
            accept=".csv"
            className="hidden"
            ref={setFileInput}
            onChange={handleFileUpload}
          />
          <Button
            variant="outline"
            onClick={() => fileInput?.click()}
          >
            <Upload className="h-4 w-4 mr-2" />
            Import CSV
          </Button>
        </div>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Full Name</TableHead>
            <TableHead>Phone Number</TableHead>
            <TableHead>Address</TableHead>
            <TableHead>Employment Status</TableHead>
            <TableHead>Monthly Income</TableHead>
            <TableHead>Active Loans</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {borrowers?.map((borrower: any) => (
            <TableRow key={borrower.id}>
              <TableCell>{borrower.fullName}</TableCell>
              <TableCell>{borrower.phoneNumber}</TableCell>
              <TableCell>{borrower.address}</TableCell>
              <TableCell>{borrower.employmentStatus}</TableCell>
              <TableCell>
                ${borrower.monthlyIncome.toLocaleString()}
              </TableCell>
              <TableCell>
                {borrower.loans?.filter((loan: any) => 
                  loan.status === "active"
                ).length || 0}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
