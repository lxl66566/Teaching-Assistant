import React from "react";
import { Card } from "@/components/ui/card";
import DocumentList from "@/components/DocumentManagement/DocumentList";

const DocumentManagementApp: React.FC = () => {
  return (
    <div className="flex min-h-screen flex-1 flex-col p-6">
      <Card className="flex h-full flex-1 flex-col rounded-xl bg-white pt-4 shadow-xl">
        <DocumentList />
      </Card>
    </div>
  );
};

export default DocumentManagementApp;
