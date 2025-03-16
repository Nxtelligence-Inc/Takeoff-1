import Image from "next/image"
import Link from "next/link"

export function Logo() {
  return (
    <Link href="/" className="flex items-center">
      <Image
        src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/logo_71ac8588-FZInvMcvr36DJnMMWdql5LrZklSDUF.svg"
        alt="Foundation Plan Analyzer Logo"
        width={180}
        height={40}
        className="h-10 w-auto"
      />
    </Link>
  )
}

