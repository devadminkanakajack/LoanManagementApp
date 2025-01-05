import { useQuery } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function Analytics() {
  const { data: analyticsData, isLoading } = useQuery({
    queryKey: ["analytics-data"],
    queryFn: async () => {
      const response = await fetch("/api/dashboard/analytics");
      if (!response.ok) {
        throw new Error("Failed to fetch analytics data");
      }
      return response.json();
    },
  });

  if (isLoading) {
    return <AnalyticsSkeleton />;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
      
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Loan Approval Rate</CardTitle>
          </CardHeader>
          <CardContent className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={analyticsData?.approvalRate || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="period" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="rate" 
                  stroke="hsl(var(--primary))" 
                  strokeWidth={2} 
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Default Rate Trend</CardTitle>
          </CardHeader>
          <CardContent className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={analyticsData?.defaultRate || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="period" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="rate" 
                  stroke="hsl(var(--destructive))" 
                  strokeWidth={2} 
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function AnalyticsSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-48" />
      <div className="grid gap-4 md:grid-cols-2">
        {[...Array(2)].map((_, i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-6 w-32" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-[300px] w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
