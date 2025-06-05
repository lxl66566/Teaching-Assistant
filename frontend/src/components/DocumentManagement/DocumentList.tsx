import React, { useState, useEffect } from "react";
import { CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Trash2, Plus, FileText, FileSpreadsheet, File, FileCode, FileImage, RefreshCcw, Loader2, Pencil } from "lucide-react";
import { Button } from "../ui/button";
import { FileUploadModal } from "./FileUploadModal";
import { cn } from "@/lib/utils";
import { useToast } from "@/components/ui/use-toast";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { knowledgeAPI } from "@/lib/api";
import { Checkbox } from "@/components/ui/checkbox";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Document } from "@/types/document";

const DocumentList = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const { toast } = useToast();
  const [isRenamingId, setIsRenamingId] = useState<string | null>(null);
  const [isLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  // Add a new state for tracking the last selected index
  const [lastSelectedIndex, setLastSelectedIndex] = useState<number | null>(null);

  const fetchDocuments = async () => {
    const res = await knowledgeAPI.getKnowledgeList();
    console.log("服务器返回值", res);
    setDocuments(res);
  };

  // 初始化时获取所有数据
  useEffect(() => {
    fetchDocuments();
  }, []);

  const getFileIcon = (item: Document) => {
    const extension = item.type;
    switch (extension) {
      case "pdf":
        return FileText;
      case "xlsx":
      case "xls":
      case "csv":
        return FileSpreadsheet;
      case "md":
      case "markdown":
        return FileCode;
      case "docx":
      case "doc":
        return FileText;
      case "txt":
        return FileText;
      case "jpg":
      case "jpeg":
      case "png":
        return FileImage;
      default:
        return File;
    }
  };

  const handleRenameDocument = (docId: string, newName: string) => {
    knowledgeAPI
      .updateDocument(docId, newName, undefined)
      .then((res) => {
        console.log("更新文档状态结果", res);
        setDocuments(documents.map((doc) => (doc.id === docId ? { ...doc, filename: newName } : doc)));
        toast({
          title: "Success",
          description: "文档重命名成功",
        });
      })
      .catch((err) => {
        toast({
          title: "Error",
          description: err.message,
        });
      })
      .finally(() => {
        setIsRenamingId(null);
      });
  };

  const handleUpload = async (files: FileList) => {
    // 转换 FileList 为数组以便处理
    const fileArray = Array.from(files);

    try {
      // 并行上传所有文件
      const uploadPromises = fileArray.map(async (file) => {
        // 根据文件扩展名判断类型
        const fileType = file.name.split(".").pop()?.toLowerCase() || "";

        try {
          const result = await knowledgeAPI.uploadDocument(
            file,
            fileType,
            `Uploaded file: ${file.name}`, // 简单的描述
          );

          return {
            fileName: file.name,
            status: "success",
            data: result,
          };
        } catch (error) {
          return {
            fileName: file.name,
            status: "error",
            error: error instanceof Error ? error.message : "上传失败",
          };
        }
      });

      // 等待所有上传完成
      const results = await Promise.all(uploadPromises);

      // 处理上传结果
      results.forEach((result) => {
        if (result.status === "success") {
          setDocuments([...documents, result.data]);
          console.log(`文件 ${result.fileName} 上传成功`);
          toast({
            title: "Success",
            description: `文件 ${result.fileName} 上传成功`,
          });
        } else {
          console.error(`文件 ${result.fileName} 上传失败:`, result.error);
          toast({
            title: "Error",
            description: `文件 ${result.fileName} 上传失败: ${result.error}`,
          });
        }
      });
    } catch (error) {
      console.error("文件上传过程出错:", error);
      toast({
        title: "Error",
        description: `文件上传失败: ${error}`,
      });
    }
  };

  const handleDelete = async (docId: string) => {
    const res = await knowledgeAPI.deleteDocument(docId);
    console.log("删除文档结果", res);
    if (res.success) {
      setDocuments(documents.filter((doc) => doc.id !== docId));
      toast({
        title: "Success",
        description: "文档删除成功",
      });
    } else {
      toast({
        title: "Error",
        description: "文档删除失败",
      });
    }
  };

  // 防抖
  const [isEnabling, setIsEnabling] = useState<string | null>(null);
  const enableDocument = async (doc: Document, checked: boolean) => {
    try {
      // Prevent double-calling this function
      if (isEnabling === doc.id) {
        console.log(`Already processing document ${doc.id}`);
        return;
      }
      setIsEnabling(doc.id);
      knowledgeAPI.updateDocument(doc.id, undefined, checked).then((res) => {
        setIsEnabling(null);
        console.log("更新文档状态结果", res);
        if (!res.enabled) {
          doc.enabled = false;
          toast({
            title: "文档已禁用",
            description: "文档已成功禁用",
          });
        } else {
          doc.enabled = true;
          toast({
            title: "文档已启用",
            description: `文档已成功启用。`,
          });
        }
      });
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : `文档 ${checked ? "启用" : "删除"} 失败`,
        variant: "danger",
      });
    }
  };

  // New handler for checkbox clicks to support shift-range selection
  const handleCheckboxClick = (docId: string, index: number, event: React.MouseEvent) => {
    event.stopPropagation();
    const isSelected = selectedIds.has(docId);

    if (event.shiftKey && lastSelectedIndex !== null) {
      // Select range from lastSelectedIndex to current index
      const start = Math.min(lastSelectedIndex, index);
      const end = Math.max(lastSelectedIndex, index);
      const newSet = new Set(selectedIds);
      for (let i = start; i <= end; i++) {
        newSet.add(documents[i].id);
      }
      setSelectedIds(newSet);
    } else {
      // Toggle current selection
      const newSet = new Set(selectedIds);
      if (isSelected) {
        newSet.delete(docId);
      } else {
        newSet.add(docId);
      }
      setSelectedIds(newSet);
      setLastSelectedIndex(index);
    }
  };

  const [toggleLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const handleMultipleDelete = async () => {
    const selectedDocs = documents.filter((doc) => selectedIds.has(doc.id));

    if (!window.confirm(`你确定要删除这 ${selectedDocs.length} 个文件/文件夹吗`)) {
      return;
    }

    setDeleteLoading(true);

    toast({
      title: "正在删除文档",
      description: `正在删除 ${selectedDocs.length} 个文档...`,
    });

    try {
      // 并行删除所有文档
      const deleteResults = await Promise.allSettled(selectedDocs.map((doc) => knowledgeAPI.deleteDocument(doc.id)));

      // 统计删除结果
      const failedCount = deleteResults.filter((result) => result.status === "rejected").length;
      const successIds = deleteResults.filter((result) => result.status === "fulfilled").map((result) => result.value);

      if (failedCount > 0) {
        toast({
          variant: "danger",
          title: "删除部分完成",
          description: `${selectedDocs.length - failedCount} 个文档删除成功，${failedCount} 个失败`,
        });
        setDocuments(documents.filter((doc) => !successIds.includes(doc.id)));
      } else {
        toast({
          title: "删除成功",
          description: `成功删除 ${selectedDocs.length} 个文档`,
        });
        setDocuments(documents.filter((doc) => !successIds.includes(doc.id)));
      }
    } catch (error) {
      toast({
        variant: "danger",
        title: "错误",
        description: "删除过程中发生错误：" + (error instanceof Error ? error.message : "未知错误"),
      });
    }
  };

  // Function to toggle enable/disable for multiple documents
  const toggleEnableMultiple = async (enable: boolean) => {
    try {
      // 创建一个 Promise 数组来存储所有的更新操作
      const updatePromises = Array.from(selectedIds).map(async (id) => {
        try {
          const response = await knowledgeAPI.updateDocument(id, undefined, enable);
          return { id, success: true, response };
        } catch (error) {
          return { id, success: false, error };
        }
      });

      // 等待所有更新操作完成
      const results = await Promise.all(updatePromises);

      // 统计成功和失败的数量
      const successCount = results.filter((r) => r.success).length;
      const failureCount = results.filter((r) => !r.success).length;

      // 更新本地文档状态
      const updatedDocs = documents.map((doc) => {
        if (selectedIds.has(doc.id)) {
          return { ...doc, enabled: enable };
        }
        return doc;
      });
      setDocuments(updatedDocs);

      // 清空选择
      setSelectedIds(new Set());

      // 显示操作结果
      if (successCount > 0) {
        toast({
          title: enable ? "文档已启用" : "文档已删除",
          description: `成功 ${enable ? "启用" : "删除"} ${successCount} 个文档。`,
        });
      }

      if (failureCount > 0) {
        toast({
          title: "Warning",
          description: `${enable ? "启用" : "删除"} ${failureCount} 个文档失败。`,
          variant: "danger",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : `更新文档失败`,
        variant: "danger",
      });
    }
  };

  return (
    <div className="relative">
      <CardContent>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Input placeholder="搜索文档..." className="h-9 w-[200px]" onChange={() => {}} />
          </div>
          <div className="flex items-center gap-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="outline" size="sm" className="h-9" onClick={fetchDocuments}>
                    <RefreshCcw className={cn("h-4 w-4 mr-2", isLoading && "animate-spin")} />
                    刷新
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>刷新文件列表</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <Button variant="default" size="sm" className="h-9" onClick={() => setIsUploadModalOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              上传
            </Button>
          </div>
        </div>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-8">
                <Checkbox
                  checked={selectedIds.size === documents.length && documents.length > 0}
                  onCheckedChange={(checked) => {
                    if (checked) {
                      setSelectedIds(new Set(documents.map((doc) => doc.id)));
                    } else {
                      setSelectedIds(new Set());
                    }
                  }}
                />
              </TableHead>
              <TableHead>文件名</TableHead>
              <TableHead>Chunk 数量</TableHead>
              <TableHead>上传日期</TableHead>
              <TableHead>是否使用</TableHead>
              <TableHead>解析状态</TableHead>
              <TableHead className="w-[100px]">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {documents.map((doc: Document, index) => (
              <TableRow key={doc.id} className={cn("hover:bg-gray-50", doc.type === "folder" && "cursor-pointer")} draggable={false} onClick={() => {}}>
                <TableCell className="w-8">
                  <div onClick={(e) => handleCheckboxClick(doc.id, index, e)}>
                    <Checkbox checked={selectedIds.has(doc.id)} />
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    {React.createElement(getFileIcon(doc))}
                    {isRenamingId === doc.id ? (
                      <Input
                        autoFocus
                        defaultValue={doc.filename}
                        className="h-8 w-[200px]"
                        onBlur={(e) => handleRenameDocument(doc.id, e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            handleRenameDocument(doc.id, e.currentTarget.value);
                          } else if (e.key === "Escape") {
                            setIsRenamingId(null);
                          }
                        }}
                      />
                    ) : (
                      <div className="flex items-center gap-2">
                        <span className={cn("cursor-pointer", doc.type === "folder" && "font-medium hover:underline")} onClick={() => {}}>
                          {doc.filename}
                        </span>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6 opacity-0 group-hover:opacity-100"
                          onClick={(e) => {
                            e.stopPropagation();
                            setIsRenamingId(doc.id);
                          }}
                        >
                          <Pencil className="h-3 w-3" />
                        </Button>
                      </div>
                    )}
                  </div>
                </TableCell>
                <TableCell>{doc.chunk_size}</TableCell>
                <TableCell>{doc.created_at}</TableCell>
                <TableCell>
                  <Switch
                    checked={doc.enabled}
                    disabled={isEnabling === doc.id}
                    onCheckedChange={(checked) => {
                      // Skip if already processing
                      if (isEnabling === doc.id) {
                        return;
                      }
                      // Then trigger the API call
                      enableDocument(doc, checked).catch((error) => {
                        // Error handling is done in enableDocument
                        // This try/catch is just to prevent unhandled rejections
                        console.error("Error toggling document:", error);
                      });
                    }}
                    aria-label="Toggle document embedding"
                  />
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <Badge
                      variant="outline"
                      className={cn(
                        doc.status === "completed" && "bg-green-100 text-green-800 border-green-200",
                        doc.status === "failed" && "bg-red-100 text-red-800 border-red-200",
                        doc.status === "pending" && "bg-orange-100 text-orange-800 border-orange-200",
                        !doc.status && "bg-gray-100 text-gray-800 border-gray-200",
                      )}
                    >
                      {doc.status || "Unparsed"}
                    </Badge>
                  </div>
                </TableCell>
                <TableCell>
                  {/* For documents, show the existing document actions */}
                  <div className="flex items-center justify-center gap-2">
                    {/* Rename button */}
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            id={`rename-button-${doc.id}`}
                            variant="ghost"
                            size="icon"
                            onClick={(e) => {
                              e.stopPropagation();
                              setIsRenamingId(doc.id);
                            }}
                            className="h-8 w-8"
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>重命名文档</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>

                    {/* Delete button */}
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            id={`delete-button-${doc.id}`}
                            variant="ghost"
                            size="icon"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(doc.id);
                            }}
                            className="h-8 w-8 hover:bg-red-100 hover:text-red-600"
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>删除文档</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        {/* Bottom action bar for multi-select */}
        {selectedIds.size > 0 && (
          <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 bg-white border rounded-lg shadow-lg flex items-center z-50">
            <div className="flex items-center py-2 px-4 border-r">
              <span className="font-medium">已选择 {selectedIds.size} 个文档</span>
            </div>

            <div className="flex items-center gap-8 p-2">
              <div className="flex items-center">
                <span className="mr-3">启用/禁用</span>
                <Switch
                  checked={selectedIds.size > 0 && documents.filter((doc) => selectedIds.has(doc.id)).every((doc) => doc.enabled)}
                  onCheckedChange={(checked) => {
                    // Disable during operation to prevent double-clicks
                    if (toggleLoading) return;

                    toggleEnableMultiple(checked);
                  }}
                  disabled={toggleLoading}
                />
              </div>

              <Button size="sm" variant="destructive" className="flex items-center" onClick={handleMultipleDelete} disabled={deleteLoading}>
                {deleteLoading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Trash2 className="h-4 w-4 mr-2" />}
                删除文档
              </Button>
            </div>
          </div>
        )}

        <FileUploadModal isOpen={isUploadModalOpen} onClose={() => setIsUploadModalOpen(false)} onUpload={handleUpload} />

        {/* <AlertDialog open={showReindexDialog} onOpenChange={setShowReindexDialog}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>{selectedDocument && getReindexWarningContent(selectedDocument).title}</AlertDialogTitle>
              <AlertDialogDescription>{selectedDocument && getReindexWarningContent(selectedDocument).description}</AlertDialogDescription>
            </AlertDialogHeader>

            {isReindexing && (
              <div className="space-y-2 my-4">
                <div className="text-sm text-muted-foreground">{progressStatus}</div>
                <Progress value={reindexProgress} className="w-full" />
              </div>
            )}

            <AlertDialogFooter>
              <AlertDialogCancel onClick={() => setShowReindexDialog(false)} disabled={isReindexing}>
                Cancel
              </AlertDialogCancel>
              <AlertDialogAction onClick={handleReindexConfirm} className="bg-primary text-white hover:bg-primary/90" disabled={isReindexing}>
                {isReindexing ? "Processing..." : "Proceed"}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog> */}
      </CardContent>
    </div>
  );
};

export default DocumentList;
