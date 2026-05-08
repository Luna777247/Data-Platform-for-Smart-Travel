"use client"

import React from "react"

interface ClientRootProps {
  children: React.ReactNode
}

// Stubbed client root: the aggressive DOM-cleanup feature was removed per
// user request. Keep a trivial client wrapper so imports remain valid.
export default function ClientRoot({ children }: ClientRootProps) {
  // No DOM mutation or cleanup performed here anymore.
  return <>{children}</>
}
