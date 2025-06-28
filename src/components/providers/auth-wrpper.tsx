"use client"

import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useEffect, type ReactNode } from "react"
import { Loader2 } from "lucide-react"

interface AuthWrapperProps {
  children: ReactNode
  requireAuth?: boolean
}

export function AuthWrapper({ children, requireAuth = true }: AuthWrapperProps) {
  const { data: session, status } = useSession()
  const router = useRouter()

  useEffect(() => {
    if (requireAuth && status === "unauthenticated") {
      router.push("/login")
    }
  }, [status, requireAuth, router])

  if (requireAuth && status === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">กำลังตรวจสอบการเข้าสู่ระบบ...</p>
        </div>
      </div>
    )
  }

  if (requireAuth && !session) {
    return null
  }

  return <>{children}</>
}