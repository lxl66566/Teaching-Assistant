import ChatApp from "@/pages/ChatApp";
import DocumentManagementApp from "@/pages/DocumentManagementApp";
import { Routes, Route } from "react-router-dom";
import { MainLayout } from "@/MainLayout";
import { Toaster } from "@/components/ui/toaster";
import ModelConfigPage from "./pages/ModelConfigPage";

function App() {
  return (
    <>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/" element={<ChatApp />} />
          <Route path="/documents" element={<DocumentManagementApp />} />
          <Route path="/model-config" element={<ModelConfigPage />} />

          {/* Settings Routes */}
          {/* <Route path="/settings" element={<SettingsPage />}>
            <Route index element={<GeneralSettings />} />
            <Route path="billing" element={<div className="p-8">Billing settings coming soon</div>} />
            <Route path="sso" element={<div className="p-8">SSO settings coming soon</div>} />
            <Route path="projects" element={<div className="p-8">Projects settings coming soon</div>} />
          </Route> */}
          <Route path="*" element={<div className="p-8 text-center">Page Not Found</div>} />
        </Route>
      </Routes>
      <Toaster />
    </>
  );
}

export default App;
