import React from "react";
import { Card } from "@/components/ui/card";
import { Toaster } from "@/components/ui/toaster";
import DocumentList from "@/components/DocumentManagement/DocumentList";

const DocumentManagementApp: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex-1 p-6">
        <Card className="bg-white shadow-xl rounded-xl h-full flex flex-col pt-4">
          <DocumentList />
        </Card>
      </div>
      <Toaster />
    </div>
  );
};

export default DocumentManagementApp;
