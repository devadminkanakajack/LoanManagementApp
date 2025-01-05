import { Link } from "wouter";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";
import { Settings, HelpCircle, LogOut, User } from "lucide-react";

export default function TopNav() {
  const { user, logout } = useAuth();

  return (
    <header className="h-16 border-b border-border bg-background">
      <div className="container h-full flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/dashboard">
            <img
              src="https://via.placeholder.com/40x40"
              alt="K&R Financial"
              className="h-10 w-10"
            />
          </Link>
        </div>

        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon">
            <HelpCircle className="h-5 w-5" />
          </Button>
          
          <Button variant="ghost" size="icon">
            <Settings className="h-5 w-5" />
          </Button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="relative h-10 w-10 rounded-full">
                <User className="h-5 w-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem className="font-medium">
                {user?.username}
              </DropdownMenuItem>
              <DropdownMenuItem onClick={logout}>
                <LogOut className="mr-2 h-4 w-4" />
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}
