
import React from "react"

interface ClientRootProps {
  children: React.ReactNode
}

export default function ClientRoot({ children }: ClientRootProps) {
  return <>{children}</>
}
