import React from 'react';

import { useAuthRedirect } from '@/hooks/auth/useAuthRedirect';
import { render, screen } from '@testing-library/react';

import SignInPage from '../page';

jest.mock('@/app/firebase/config', () => ({
  auth: {},
  db: {}
}))
jest.mock('@/hooks/auth/useAuthRedirect');
jest.mock('@/components/auth/AuthLayout', () => ({
  AuthLayout: ({ children, title, description }: { children: React.ReactNode, title: string, description: string }) => (
    <div>
      <h1>{title}</h1>
      <p>{description}</p>
      {children}
    </div>
  ),
}));
jest.mock('@/components/auth/GoogleSignIn', () => ({
  GoogleSignInButton: () => <button>Sign in with Google</button>,
}));
jest.mock('@/components/auth/OrSeperator', () => ({
  OrSeparator: ({ text }: { text: string }) => <div>{text}</div>,
}));
jest.mock('@/components/auth/signin/SignInForm', () => ({
  SignInForm: () => <form>Sign In Form</form>,
}));
jest.mock('@/components/auth/AuthLink', () => ({
  AuthLink: ({ children, href }: { children: React.ReactNode, href: string }) => <a href={href}>{children}</a>,
}));


describe('SignInPage', () => {
  const mockUseAuthRedirect = useAuthRedirect as jest.Mock;

  it('should return null when loading', () => {
    mockUseAuthRedirect.mockReturnValue({ loading: true });
    const { container } = render(<SignInPage />);
    expect(container.firstChild).toBeNull();
  });

  it('should render the sign-in page when not loading', () => {
    mockUseAuthRedirect.mockReturnValue({ loading: false });
    render(<SignInPage />);

    expect(screen.getByText('Welcome back')).toBeInTheDocument();
    expect(screen.getByText('Sign in to your Mifos Assistant account')).toBeInTheDocument();
    expect(screen.getByText('Sign in with Google')).toBeInTheDocument();
    expect(screen.getByText('Or continue with email')).toBeInTheDocument();
    expect(screen.getByText('Sign In Form')).toBeInTheDocument();
    expect(screen.getByText(/Don’t have an account?/)).toBeInTheDocument();
    expect(screen.getByText('Sign up')).toBeInTheDocument();
    expect(screen.getByText('Forgot your password?')).toBeInTheDocument();
  });
});
