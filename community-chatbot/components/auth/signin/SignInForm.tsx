"use client"

import { Loader2, Lock, Mail } from 'lucide-react';
import { useForm } from 'react-hook-form';

import { FormField } from '@/components/auth/FormField';
import { Button } from '@/components/ui/button';
import { useSignIn } from '@/hooks/auth/signin/useSignIn';
import { signInSchema, SignInSchema } from '@/types/auth/schema';
import { zodResolver } from '@hookform/resolvers/zod';

export function SignInForm() {
	const { signIn } = useSignIn()

	const {
		register,
		handleSubmit,
		formState: { errors, isSubmitting },
	} = useForm<SignInSchema>({
		resolver: zodResolver(signInSchema),
	})

	const onSubmit = handleSubmit(signIn)

	return (
		<form onSubmit={onSubmit} className="space-y-4">
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
