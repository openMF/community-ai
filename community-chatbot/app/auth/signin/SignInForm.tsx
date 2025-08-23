"use client"

import { useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { Loader2, Lock, Mail } from "lucide-react"
import { signInWithEmailAndPassword } from "firebase/auth"

import { auth } from "@/app/firebase/config"
import { Button } from "@/components/ui/button"
import { FormField } from "@/components/auth/FormField"
import { useToast } from "@/hooks/use-toast"

import { signInSchema, SignInSchema } from "@/types/auth/signin/schema"

export function SignInForm() {
    const router = useRouter()
    const { toast } = useToast()

    const {
        register,
        handleSubmit,
        formState: { errors, isSubmitting },
    } = useForm<SignInSchema>({
        resolver: zodResolver(signInSchema),
    })

    const onSubmit = async (data: SignInSchema) => {
        try {
            await signInWithEmailAndPassword(auth, data.email, data.password)
            router.push("/")
            toast({
                title: "Welcome back!",
                description: "Signed in successfully."
            })
        } catch (err: any) {
            toast({
                variant: "destructive",
                title: "Sign in failed",
                description: err.message || "Something went wrong.",
            })
        }
    }

    return (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <FormField
                id="email"
                label="Email"
                type="email"
                placeholder="Enter your email"
                icon={<Mail className="w-4 h-4" />}
                register={register}
                error={errors.email?.message}
            />

            <FormField
                id="password"
                label="Password"
                type="password"
                placeholder="Enter your password"
                icon={<Lock className="w-4 h-4" />}
                register={register}
                error={errors.password?.message}
            />

            <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? (
                    <>
                        <Loader2 className="mr-2 w-4 h-4 animate-spin" />
                        Signing in...
                    </>
                ) : (
                    "Sign in"
                )}
            </Button>
        </form>
    )
}
