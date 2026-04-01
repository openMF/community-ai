"use client";

import { ChatHistory } from '@/components/agent/Sidebar/ChatHistory';
import { NewChatButton } from '@/components/agent/Sidebar/NewChatButton';
import {
    Header as SidebarHeader,
} from '@/components/agent/Sidebar/SidebarHeader';
import { Sidebar, SidebarContent } from '@/components/ui/sidebar';

export function AppSidebar() {
    return (
        <Sidebar id="app-sidebar" side="left" variant="sidebar" collapsible="icon">
            <SidebarHeader />
            <SidebarContent className="flex flex-col h-full">
                <NewChatButton />
                <ChatHistory />
            </SidebarContent>
        </Sidebar>
    )
}