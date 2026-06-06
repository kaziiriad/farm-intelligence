import { Link } from "@tanstack/react-router";
import { Sprout } from "lucide-react";
import { Toaster } from "@/components/ui/sonner";
import type { ReactNode } from "react";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <header className="border-b bg-card">
        <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between gap-4">
          <Link
            to="/"
            className="flex items-center gap-2 font-semibold tracking-tight"
          >
            <Sprout className="h-5 w-5 text-primary" />
            <span>Farm Intelligence</span>
          </Link>
          <MainNav />
        </div>
      </header>
      <main className="flex-1 mx-auto w-full max-w-6xl px-4 py-6">
        {children}
      </main>
      <Toaster richColors position="top-right" />
    </div>
  );
}

export function MainNav() {
  const linkCls =
    "px-3 py-1.5 text-sm rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors";
  const activeCls = "text-foreground bg-accent font-medium";
  return (
    <nav className="flex items-center gap-1">
      <Link
        to="/"
        className={linkCls}
        activeProps={{ className: `${linkCls} ${activeCls}` }}
        activeOptions={{ exact: true }}
      >
        Dashboard
      </Link>
      <Link
        to="/farms"
        className={linkCls}
        activeProps={{ className: `${linkCls} ${activeCls}` }}
      >
        Farms
      </Link>
      <Link
        to="/usage"
        className={linkCls}
        activeProps={{ className: `${linkCls} ${activeCls}` }}
      >
        Usage
      </Link>
    </nav>
  );
}
