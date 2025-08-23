"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { auth } from "@/app/firebase/config"
import { onAuthStateChanged } from "firebase/auth"
import Link from "next/link"

import { AuthLayout } from "@/components/auth/AuthLayout"
import { GoogleSignInButton } from "@/components/auth/GoogleSignIn"
import { SignUpForm } from "@/app/auth/signup/SignUpForm"
import { Separator } from "@/components/ui/separator"

export default function SignUpPage() {
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
      title="Create your account"
      description="Get started with Mifos Assistant"
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

      <SignUpForm />

      <div className="text-sm text-center">
        <span className="text-muted-foreground">Already have an account? </span>
        <Link href="/auth/signin" className="font-medium text-blue-600 hover:underline">
          Sign in
        </Link>
      </div>
    </AuthLayout>
  )
}