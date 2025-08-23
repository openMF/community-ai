"use client"

import { useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { Loader2, Lock, Mail, User } from "lucide-react"
import { createUserWithEmailAndPassword, updateProfile } from "firebase/auth"

import { auth } from "@/app/firebase/config"
import { Button } from "@/components/ui/button"
import { FormField } from "@/components/auth/FormField"
import { Checkbox } from "@/components/ui/checkbox"
import { useToast } from "@/hooks/use-toast"
import Link from "next/link"

import { signUpSchema, SignUpSchema } from "@/types/auth/signup/schema"

export function SignUpForm() {
    const router = useRouter()
    const { toast } = useToast()

    const {
        register,
        handleSubmit,
        formState: { errors, isSubmitting },
        setValue,
    } = useForm<SignUpSchema>({
        resolver: zodResolver(signUpSchema),
    })

    const onSubmit = async (data: SignUpSchema) => {
        try {
            const userCredential = await createUserWithEmailAndPassword(auth, data.email, data.password)
            await updateProfile(userCredential.user, {
                displayName: data.name,
            })
            router.push("/")
            toast({
                title: "Welcome!",
                description: "Account created successfully."
            })
        } catch (err: any) {
            toast({
                variant: "destructive",
                title: "Sign up failed",
                description: err.message || "Something went wrong.",
            })
        }
    }

    return (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <FormField
                id="name"
                label="Full Name"
                type="text"
                placeholder="Enter your full name"
                icon={<User className="w-4 h-4" />}
                register={register}
                error={errors.name?.message}
            />

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
                placeholder="Create a password"
                icon={<Lock className="w-4 h-4" />}
                register={register}
                error={errors.password?.message}
            />
            <p className="text-muted-foreground text-xs">Must be at least 8 characters long</p>

            <FormField
                id="confirmPassword"
                label="Confirm Password"
                type="password"
                placeholder="Confirm your password"
                icon={<Lock className="w-4 h-4" />}
                register={register}
                error={errors.confirmPassword?.message}
            />

            <div className="flex items-center space-x-2">
                <Checkbox
                    id="terms"
                    onCheckedChange={(checked) => setValue("acceptTerms", !!checked)}
                />
                <label
                    htmlFor="terms"
                    className="peer-disabled:opacity-70 font-medium text-sm leading-none peer-disabled:cursor-not-allowed"
                >
                    I agree to the{" "}
                    <Link href="/terms" className="text-blue-600 hover:underline">
                        Terms of Service
                    </Link>{" "}
                    and{" "}
                    <Link href="/privacy" className="text-blue-600 hover:underline">
                        Privacy Policy
                    </Link>
                </label>
            </div>
            {errors.acceptTerms && <p className="text-red-500 text-sm">{errors.acceptTerms.message}</p>}

            <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? (
                    <>
                        <Loader2 className="mr-2 w-4 h-4 animate-spin" />
                        Creating account...
                    </>
                ) : (
                    "Create account"
                )}
            </Button>
        </form>
    )
}