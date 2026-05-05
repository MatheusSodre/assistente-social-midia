import { LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";

export function Topbar() {
  const { user, signOut, bypassed } = useAuth();

  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-background px-6">
      <div className="flex items-center gap-3">
        {bypassed && (
          <span className="rounded-full bg-primary/15 px-2 py-0.5 text-xs font-medium text-primary">
            DEV BYPASS
          </span>
        )}
      </div>
      <div className="flex items-center gap-3 text-sm">
        <span className="text-muted-foreground">{user?.email}</span>
        {!bypassed && (
          <Button variant="ghost" size="sm" onClick={() => void signOut()}>
            <LogOut className="mr-1 h-4 w-4" />
            Sair
          </Button>
        )}
      </div>
    </header>
  );
}
