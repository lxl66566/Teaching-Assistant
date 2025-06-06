import { Sidebar } from "@/components/layout/Sidebar";
import { Navbar } from "@/components/layout/Navbar";
import { Outlet } from "react-router-dom";
import { ModeProvider } from "@/context/ModeContext"; // 导入 ModeProvider

export function MainLayout() {
  return (
    <div className="flex h-screen w-screen max-w-[100vw] overflow-auto bg-zinc-50">
      <Sidebar />
      <ModeProvider>
        <div className="flex flex-col flex-1 min-w-0">
          <Navbar />
          <main className="flex flex-1 overflow-auto p-0">
            <Outlet />
          </main>
        </div>
      </ModeProvider>
    </div>
  );
}
