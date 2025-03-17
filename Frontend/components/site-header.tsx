import type React from "react"
import Link from "next/link"
import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Settings, ArrowLeft } from "lucide-react"

interface SiteHeaderProps {
  showBackButton?: boolean
  backHref?: string
  rightContent?: React.ReactNode
}

export function SiteHeader({ showBackButton = false, backHref = "/", rightContent }: SiteHeaderProps) {
  return (
    <header className="sticky top-0 z-10 border-b bg-background">
      <div
        className="container flex items-center justify-between px-4 md:px-6 lg:px-8"
        style={{ paddingTop: "16px", paddingBottom: "16px" }}
      >
        <div className="flex items-center gap-2">
          {showBackButton && (
            <Link href={backHref}>
              <Button variant="ghost" size="icon">
                <ArrowLeft className="h-5 w-5" />
              </Button>
            </Link>
          )}
          <Link href="/">
            <Image
              src="/logos/nxtelligence-logo-black.png"
              alt="NxTelligence Logo"
              width={180}
              height={52}
              priority
            />
          </Link>
        </div>
        <div className="flex items-center gap-4">
          {rightContent || (
            <Link href="/settings">
              <Button variant="ghost" size="icon">
                <Settings className="h-5 w-5" />
                <span className="sr-only">Settings</span>
              </Button>
            </Link>
          )}
        </div>
      </div>
    </header>
  )
}
