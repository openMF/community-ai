import { createUserWithEmailAndPassword, updateProfile } from 'firebase/auth';
import { useRouter } from 'next/navigation';

import { auth } from '@/app/firebase/config';
import { useToast } from '@/hooks/use-toast';
import type { SignUpSchema } from '@/types/auth/schema';

export function useSignUp() {
    const router = useRouter()
    const { toast } = useToast()

    const signUp = async (data: SignUpSchema) => {
        try {
            const userCredential = await createUserWithEmailAndPassword(auth, data.email, data.password)
            await updateProfile(userCredential.user, { displayName: data.name })
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

    return { signUp }
}