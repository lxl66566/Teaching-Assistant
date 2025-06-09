import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Home,
  Terminal,
  Key,
  Search,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useState } from "react";
import { config } from "@/config";

// App version - in a real app this would come from environment variables or build config
const APP_VERSION = "v0.1.0";

const sidebarItems = [
  { name: "Home", icon: Home, path: "/" },
  { name: "Documents", icon: Terminal, path: "/documents" },
  { name: "API Keys", icon: Key, path: "/model-config" },
];

// const bottomItems = [{ name: "Settings", icon: Settings, path: "/settings" }];

export function Sidebar() {
  const location = useLocation();
  const [expanded, setExpanded] = useState(true);

  return (
    <div
      className={cn(
        "relative flex h-screen flex-col justify-between border-r bg-gray-50 pb-4 text-gray-700 transition-all duration-300",
        expanded ? "w-56" : "w-16",
      )}
    >
      {/* Logo and Version */}
      <div className="flex h-16 items-center justify-center border-b border-gray-200 px-4">
        {expanded ? (
          <div className="flex items-center">
            <span className="text-xl font-semibold">{config.appName}</span>
            <span className="ml-2 text-xs text-gray-500">{APP_VERSION}</span>
          </div>
        ) : null}

        {/* Toggle Button - Integrated in header */}
        <Button
          variant="ghost"
          size="sm"
          className="mx-2 h-8 w-8 rounded-md p-0 hover:bg-gray-100"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? (
            <PanelLeftClose className="h-4 w-4" />
          ) : (
            <PanelLeftOpen className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Main Navigation */}
      <div className="flex-1 overflow-auto py-4">
        <div className={cn("space-y-1", expanded ? "px-3" : "px-2")}>
          {sidebarItems.map((item) => (
            <Link key={item.name} to={item.path}>
              <Button
                variant="ghost"
                size="sm"
                className={cn(
                  "w-full justify-start text-gray-700 hover:bg-gray-100 hover:text-gray-900",
                  location.pathname === item.path &&
                    "bg-gray-100 font-medium text-gray-900",
                  expanded ? "" : "justify-center px-2",
                )}
              >
                <item.icon className={cn("h-5 w-5", expanded ? "mr-3" : "")} />
                {expanded && item.name}
              </Button>
            </Link>
          ))}
        </div>
      </div>

      {/* Bottom Navigation */}
      {/* <div className={cn("space-y-1 border-t border-gray-200 pt-3 mt-auto", expanded ? "px-3" : "px-2")}>
        {bottomItems.map((item) => (
          <Link key={item.name} to={item.path}>
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                "w-full justify-start text-gray-700 hover:text-gray-900 hover:bg-gray-100",
                location.pathname === item.path && "bg-gray-100 text-gray-900 font-medium",
                expanded ? "" : "justify-center px-2",
              )}
            >
              <item.icon className={cn("h-5 w-5", expanded ? "mr-3" : "")} />
              {expanded && item.name}
            </Button>
          </Link>
        ))}
      </div> */}

      {/* User Section */}
      <div
        className={cn(
          "mt-2 border-t border-gray-200 pt-3",
          expanded ? "px-3" : "px-2",
        )}
      >
        <DropdownMenu>
          <DropdownMenuTrigger asChild></DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>My Account</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>Profile</DropdownMenuItem>
            <DropdownMenuItem>Settings</DropdownMenuItem>
            <DropdownMenuSeparator />
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}
