'use client';

import React, { useEffect } from 'react';

import { ChatHeader } from '@/components/agent/Header';
import { ModeSelector } from '@/components/agent/ModeSelector';
import { AppSidebar } from '@/components/agent/Sidebar';
import { AppTour } from '@/components/agent/AppTour';
import { useAgentStore } from '@/lib/store/agent/agentStore';

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    const { initAuth } = useAgentStore();

    useEffect(() => {
        const unsubscribe = initAuth();
        return () => unsubscribe();
    }, [initAuth]);

    return (
        <main className="flex w-full h-screen">
            <AppTour />
            <AppSidebar />
            <div className="flex flex-col w-full">
                <ChatHeader />
                <ModeSelector />
                {children}
            </div>
        </main>
    )
}