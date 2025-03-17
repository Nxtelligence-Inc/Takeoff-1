import Image from "next/image"
import Link from "next/link"

export function Logo() {
  return (
    <Link href="/" className="flex items-center">
      <Image
        src="/logos/nxtelligence-logo-black.png"
        alt="NxTelligence Logo"
        width={180}
        height={52}
        className="h-10 w-auto"
      />
    </Link>
  )
}
