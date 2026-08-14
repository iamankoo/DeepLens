import { RequireAuth } from "@/components/auth/require-auth";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { PageTransition } from "@/components/layout/page-transition";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset>
          <PageTransition>{children}</PageTransition>
        </SidebarInset>
      </SidebarProvider>
    </RequireAuth>
  );
}
