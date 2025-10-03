import { signInWithEmailAndPassword } from 'firebase/auth';
import { useRouter } from 'next/navigation';

import { auth } from '@/app/firebase/config';
import { useToast } from '@/components/ui/use-toast';
import { SignInSchema } from '@/types/auth/schema';

export function useSignIn() {
	const { toast } = useToast()
	const router = useRouter()

	const signIn = async (data: SignInSchema) => {
		try {
			await signInWithEmailAndPassword(auth, data.email, data.password)
			router.push("/")
			toast({
				title: "Welcome back!",
				description: "Signed in successfully.",
			})
		} catch (err: any) {
			toast({
				variant: "destructive",
				title: "Sign in failed",
				description: err.message || "Something went wrong.",
			})
		}
	}

	return { signIn }
}