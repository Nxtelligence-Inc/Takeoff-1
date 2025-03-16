"use client"

import type React from "react"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { FileText, Home, Menu, Search, Settings, Upload, Database, ChevronDown, ChevronRight, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

interface NotionLayoutProps {
  children: React.ReactNode
}

export function NotionLayout({ children }: NotionLayoutProps) {
  const pathname = usePathname()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [workspacesOpen, setWorkspacesOpen] = useState(true)

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="notion-header">
        <div className="flex items-center">
          <div className="md:hidden mr-2">
            <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(!sidebarOpen)}>
              <Menu className="h-5 w-5" />
            </Button>
          </div>
          <div className="flex items-center mr-4">
            <div className="h-8 w-8 rounded bg-foreground flex items-center justify-center text-background font-weight-605 text-sm mr-2">
              F
            </div>
            <span className="hidden sm:inline font-weight-605">Foundation Analyzer</span>
          </div>
        </div>
        <div className="notion-header-content">
          <div className="flex items-center gap-4">
            <div className="relative w-full max-w-md">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search..."
                className="w-full bg-secondary pl-8 focus-visible:ring-0 border-none text-sm"
              />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" className="text-muted-foreground">
              Share
            </Button>
            <Button variant="ghost" size="sm" className="text-muted-foreground">
              Updates
            </Button>
            <Button variant="ghost" size="sm" className="text-muted-foreground">
              Comments
            </Button>
            <Button variant="ghost" size="icon" className="text-muted-foreground">
              <Settings className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </header>

      {/* Sidebar */}
      <aside className={cn("notion-sidebar", !sidebarOpen && "hidden md:block")}>
        <div className="p-4">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <div className="h-6 w-6 rounded bg-foreground flex items-center justify-center text-background font-medium text-sm">
                F
              </div>
              <span className="font-medium">Foundation Analyzer</span>
            </div>
            <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
              <ChevronDown className="h-4 w-4" />
            </Button>
          </div>

          <div className="space-y-1 mb-6">
            <Link href="/" className={cn("notion-nav-item", pathname === "/" && "active")}>
              <Home className="h-4 w-4" />
              <span>Home</span>
            </Link>
            <Link href="/analyses" className={cn("notion-nav-item", pathname.startsWith("/analyses") && "active")}>
              <FileText className="h-4 w-4" />
              <span>Analyses</span>
            </Link>
            <Link href="/analyze" className={cn("notion-nav-item", pathname === "/analyze" && "active")}>
              <Upload className="h-4 w-4" />
              <span>Analyze Plan</span>
            </Link>
            <Link href="/database" className={cn("notion-nav-item", pathname === "/database" && "active")}>
              <Database className="h-4 w-4" />
              <span>Database</span>
            </Link>
          </div>

          <div className="mb-4">
            <div
              className="flex items-center justify-between px-2 py-1 text-sm text-muted-foreground cursor-pointer"
              onClick={() => setWorkspacesOpen(!workspacesOpen)}
            >
              {workspacesOpen ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
              <span className="flex-1 ml-1">Workspaces</span>
              <Button variant="ghost" size="icon" className="h-5 w-5 p-0">
                <Plus className="h-3 w-3" />
              </Button>
            </div>

            {workspacesOpen && (
              <div className="mt-1 space-y-1 pl-4">
                <div className="notion-nav-item">
                  <div className="h-3 w-3 rounded-sm bg-blue-500"></div>
                  <span>Residential Projects</span>
                </div>
                <div className="notion-nav-item">
                  <div className="h-3 w-3 rounded-sm bg-green-500"></div>
                  <span>Commercial Projects</span>
                </div>
                <div className="notion-nav-item">
                  <div className="h-3 w-3 rounded-sm bg-orange-500"></div>
                  <span>Templates</span>
                </div>
              </div>
            )}
          </div>

          <div className="pt-4 border-t border-border/60">
            <Button variant="outline" size="sm" className="w-full justify-start text-muted-foreground">
              <Plus className="mr-2 h-4 w-4" />
              New Page
            </Button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="notion-main">
        <div className="notion-container py-8">{children}</div>
      </main>
    </div>
  )
}

