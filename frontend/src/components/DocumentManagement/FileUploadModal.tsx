import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useState, useRef } from "react";
import { Upload, Trash2 } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface FileUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (files: FileList) => void;
}

export function FileUploadModal({ isOpen, onClose, onUpload }: FileUploadModalProps) {
  const [dragActive, setDragActive] = useState(false);
  const [activeTab, setActiveTab] = useState("file");
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const addFiles = (newFiles: FileList) => {
    setSelectedFiles((prevFiles) => {
      const dt = new DataTransfer();

      // Add existing files
      if (prevFiles) {
        Array.from(prevFiles).forEach((file) => {
          dt.items.add(file);
        });
      }

      // Add new files
      Array.from(newFiles).forEach((file) => {
        dt.items.add(file);
      });

      return dt.files;
    });
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      addFiles(e.dataTransfer.files);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      addFiles(e.target.files);
    }
  };

  const removeFile = (indexToRemove: number) => {
    if (!selectedFiles) return;

    const dt = new DataTransfer();
    Array.from(selectedFiles).forEach((file, index) => {
      if (index !== indexToRemove) {
        dt.items.add(file);
      }
    });
    setSelectedFiles(dt.files);
  };

  const handleUpload = () => {
    if (selectedFiles) {
      onUpload(selectedFiles);
      setSelectedFiles(null);
      onClose();
    }
  };

  const handleAreaClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px] max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>上传文件</DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="file" className="w-full flex-1 flex flex-col">
          <TabsList className="grid w-full grid-cols-1">
            <TabsTrigger value="file">本地上传</TabsTrigger>
          </TabsList>

          <TabsContent value="file" className="flex-1 flex flex-col min-h-0">
            <div className="mt-4 space-y-4 flex-1 flex flex-col">
              <div
                className={`grid place-items-center border-2 border-dashed rounded-lg h-32 flex-shrink-0 ${
                  dragActive ? "border-primary" : "border-gray-300"
                } cursor-pointer`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={handleAreaClick}
              >
                <div className="text-center">
                  <Upload className="w-10 h-10 mx-auto text-blue-500 mb-2" />
                  <p className="text-sm text-gray-600">点击或拖拽文件到此处上传</p>
                  <p className="text-xs text-gray-500 mt-2">支持单文件或批量上传。</p>
                </div>
              </div>

              {selectedFiles && selectedFiles.length > 0 && (
                <div className="border rounded-lg shadow-sm">
                  <div className="max-h-[200px] overflow-y-auto p-2">
                    <div className="space-y-1">
                      {Array.from(selectedFiles).map((file, index) => (
                        <div key={index} className="flex items-center justify-between text-sm text-gray-600 py-1 px-2 rounded-md hover:bg-gray-100 group">
                          <div className="flex items-center gap-2 min-w-0 flex-1">
                            <svg
                              width="18"
                              height="18"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              className="text-gray-500 flex-shrink-0"
                            >
                              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
                            </svg>
                            <span className="truncate">{file.name}</span>
                          </div>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
                            onClick={(e) => {
                              e.stopPropagation();
                              removeFile(index);
                            }}
                          >
                            <Trash2 className="h-4 w-4 text-gray-500" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="directory" className="flex-1">
            <div className="mt-4 space-y-4">
              <p className="text-sm text-gray-600">Upload files from directory</p>
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter className="flex justify-between mt-6">
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          <div>
            <Input
              ref={fileInputRef}
              id="file-upload"
              type="file"
              multiple
              className="hidden"
              onChange={handleChange}
              accept=".pdf,.doc,.docx,.ppt,.pptx,.txt,.md"
              {...(activeTab === "directory" ? { webkitdirectory: "", directory: "" } : {})}
            />
            <Button onClick={handleUpload} disabled={!selectedFiles}>
              确定
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
