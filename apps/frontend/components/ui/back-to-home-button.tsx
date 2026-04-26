import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"

interface BackToHomeButtonProps {
  className?: string
}

export function BackToHomeButton({ className }: BackToHomeButtonProps) {
  return (
    <Link href="/">
      <Button variant="ghost" size="sm" className={`gap-2 ${className}`}>
        <ArrowLeft className="h-4 w-4" />
        <span className="hidden sm:inline">Back to Home</span>
      </Button>
    </Link>
  )
}
