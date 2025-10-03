"use client"

import { AuthLayout } from '@/components/auth/AuthLayout';
import { AuthLink } from '@/components/auth/AuthLink';
import { GoogleSignInButton } from '@/components/auth/GoogleSignIn';
import { OrSeparator } from '@/components/auth/OrSeperator';
import { SignUpForm } from '@/components/auth/signup/SignUpForm';
import { useAuthRedirect } from '@/hooks/auth/useAuthRedirect';

export default function SignUpPage() {
	const { loading } = useAuthRedirect()
	if (loading) return null

	return (
		<AuthLayout
			title="Create your account"
			description="Get started with Mifos Assistant"
		>
			<div className="space-y-4">
				<GoogleSignInButton />
				<OrSeparator text='Or continue with email' />
				<SignUpForm />
				<AuthLink href="/auth/signin">
					Already have an account? <span className="font-medium">Sign in</span>
				</AuthLink>
			</div>
		</AuthLayout>
	)
}