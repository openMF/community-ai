"use client"

import React, { useEffect, useState } from "react"
import { useRouter, usePathname } from "next/navigation"
import { Loader2 } from "lucide-react"
import { onAuthStateChanged } from "firebase/auth"
import { auth } from "@/app/firebase/config"
const PUBLIC_ROUTES = ["/auth/signin", "/auth/signup"]

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState<any>(null)

  const router = useRouter()
  const pathname = usePathname()
  const isPublicRoute = PUBLIC_ROUTES.includes(pathname)

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser)
      setLoading(false)

      if (!currentUser && !isPublicRoute) {
        router.push("/auth/signin")
      }
    })

    return () => unsubscribe()
  }, [router, isPublicRoute])

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-center">
          <Loader2 className="mx-auto mb-4 w-8 h-8 animate-spin" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  if (!user && !isPublicRoute) {
    return null
  }

  return <>{children}</>
}