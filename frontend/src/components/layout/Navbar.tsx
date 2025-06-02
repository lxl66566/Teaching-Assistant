import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { ChevronDown } from "lucide-react";
// import { Badge } from "@/components/ui/badge";
// import { Backend, backendList, getCurrentBackend, updateCurrentBackend } from "@/config/backend";
// import { useEffect, useState } from "react";
import { useMode } from "@/context/ModeContext";
import { AppMode } from "@/types/chat";

export function Navbar() {
  // const [currentBackend, setCurrentBackend] = useState<Backend>(getCurrentBackend());
  const { currentMode, setMode } = useMode(); // 使用 useMode Hook

  // useEffect(() => {
  //   updateCurrentBackend(currentBackend.name === backendList[0].name ? 0 : 1);
  // }, [currentBackend]);

  return (
    <div className="border-b w-full bg-white">
      <div className="flex h-16 items-center px-4 w-full">
        <div className="flex items-center">
          {/* Backend Selector */}
          {/* <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="flex items-center gap-2 mr-4 h-10">
                {currentBackend.toString()}
                <Badge variant="outline" className="ml-2 text-xs bg-gray-100">
                  {currentBackend.name}
                </Badge>
                <ChevronDown className="h-4 w-4 opacity-50" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-56">
              {backendList.map((backend, index) => (
                <DropdownMenuItem key={index} onClick={() => setCurrentBackend(backend)}>
                  {backend.name}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu> */}

          {/* Mode Selector */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="flex items-center gap-2 h-10">
                {currentMode}
                <ChevronDown className="h-4 w-4 opacity-50" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-40">
              {Object.values(AppMode).map((mode) => (
                <DropdownMenuItem key={mode} onClick={() => setMode(mode)}>
                  {mode}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </div>
  );
}
