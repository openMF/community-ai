"use client"

import React, { useEffect } from "react"
import { useRouter } from "next/navigation"
import { auth } from "@/app/firebase/config"
import { onAuthStateChanged } from "firebase/auth"
import Link from "next/link"

import { AuthLayout } from "@/components/auth/AuthLayout"
import { GoogleSignInButton } from "@/components/auth/GoogleSignIn"
import { SignInForm } from "@/app/auth/signin/SignInForm"
import { Separator } from "@/components/ui/separator"

export default function SignInPage() {
  const router = useRouter()

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      if (user) {
        router.push("/")
      }
    })

    return () => unsubscribe()
  }, [router])

  return (
    <AuthLayout
      title="Welcome back"
      description="Sign in to your Mifos Assistant account"
    >
      <GoogleSignInButton />

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <Separator className="w-full" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-background px-2 text-muted-foreground">Or continue with email</span>
        </div>
      </div>

      <SignInForm />

      <div className="text-sm text-center">
        <span className="text-muted-foreground">Don't have an account? </span>
        <Link href="/auth/signup" className="font-medium text-blue-600 hover:underline">
          Sign up
        </Link>
      </div>

      <div className="text-sm text-center">
        <Link href="/auth/forgot-password" className="text-blue-600 hover:underline">
          Forgot your password?
        </Link>
      </div>
    </AuthLayout>
  )
}