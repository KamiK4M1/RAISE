"use client"

import type React from "react"
import { useEffect } from "react"
import { SessionProvider, useSession } from "next-auth/react"
import { apiService } from "@/lib/api"

function AuthTokenSetter({ children }: { children: React.ReactNode }) {
  const { data: session } = useSession()

  useEffect(() => {
    if (session?.accessToken) {
      apiService.setAuthToken(session.accessToken as string)
    } else {
      apiService.setAuthToken(null)
    }
  }, [session])

  return <>{children}</>
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      <AuthTokenSetter>{children}</AuthTokenSetter>
    </SessionProvider>
  )
}
