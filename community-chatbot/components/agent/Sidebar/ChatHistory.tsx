'use client';

import { useState } from 'react';

import { Loader2, Pencil, Trash2 } from 'lucide-react';
import Image from 'next/image';
import { usePathname, useRouter } from 'next/navigation';

import { Button } from '@/components/ui/button';
import { SidebarGroup, useSidebar } from '@/components/ui/sidebar';
import { useDeleteConversation } from '@/hooks/agent/useDeleteConversation';
import { useFetchConversation } from '@/hooks/agent/useFetchConversation';
import { useRenameConversation } from '@/hooks/agent/useRenameConversation';
import { useAgentStore } from '@/lib/store/agent/agentStore';
import { ChatHistoryItem } from '@/types/chat/types';

export function ChatHistory() {
    const router = useRouter();
    const { open } = useSidebar();
    const pathname = usePathname();
    const currentMode = pathname.split('/')[1];
    const activeChat = pathname.split('/')[2];

    const { pendingOperations } = useAgentStore();
    const { chats, loading } = useFetchConversation();
    const { rename } = useRenameConversation();
    const { remove } = useDeleteConversation();

    const [editingId, setEditingId] = useState<string | null>(null);
    const [renameValue, setRenameValue] = useState('');

    const handleStartEditing = (chat: ChatHistoryItem) => {
        setEditingId(chat.id);
        setRenameValue(chat.title);
    };

    const handleRenameSubmit = async (chatId: string) => {
        await rename(chatId, renameValue);
        setEditingId(null);
    };

    const handleChatClick = (chatId: string, disabled: boolean) => {
        if (disabled) return;
        router.push(`/${currentMode}/${chatId}`);
    };

    if (loading) {
        return (
            <div className="flex h-full items-center justify-center">
                <Loader2 className="size-6 animate-spin" />
            </div>
        );
    }

    return (
        <SidebarGroup id="chat-history" className="space-y-4 overflow-y-auto">
            {chats?.map((chat) => {
                const isPending = pendingOperations.includes(chat.id);
                const isActive = chat.id === activeChat;
                const isEditing = editingId === chat.id;

                return (
                    <div
                        key={chat.id}
                        onClick={() => handleChatClick(chat.id, isPending || isEditing)}
                        className={`flex items-center justify-center flex-wrap gap-3 p-3 rounded-2xl transition-colors
                            ${isActive ? 'bg-blue-600 text-white' : 'hover:bg-gray-100 dark:hover:bg-gray-700'}
                            ${isPending || isEditing ? 'cursor-not-allowed opacity-70' : 'cursor-pointer'}`}
                    >
                        {/* Chat Icon */}
                        <div className="bg-white p-2 rounded-full">
                            <Image
                                src={chat.icon}
                                alt={chat.title}
                                width={20}
                                height={20}
                            />
                        </div>

                        {/* Chat Text + Rename Input */}
                        {open && (
                            <div className="flex-1 px-2 min-w-0">
                                {isEditing ? (
                                    <input
                                        value={renameValue}
                                        onChange={(e) => setRenameValue(e.target.value)}
                                        onBlur={() => handleRenameSubmit(chat.id)}
                                        onKeyDown={(e) => {
                                            if (e.key === 'Enter')
                                                handleRenameSubmit(chat.id);
                                            if (e.key === 'Escape')
                                                setEditingId(null);
                                        }}
                                        className={`w-full bg-transparent focus:outline-none ${isActive ? 'text-white' : ''}`}
                                        autoFocus
                                    />
                                ) : (
                                    <p className="font-medium truncate">{chat.title}</p>
                                )}
                                <p
                                    className={`text-xs ${isActive ? 'text-blue-100' : 'text-gray-500 dark:text-gray-400'}`}
                                >
                                    {chat.updatedAt
                                        ? new Date(chat.updatedAt).toLocaleDateString('en-GB', {
                                            day: '2-digit',
                                            month: 'short',
                                            year: 'numeric',
                                        })
                                        : ''}
                                </p>
                            </div>
                        )}

                        {/* Edit + Delete Buttons */}
                        {open && !isEditing && (
                            <div className="flex justify-center items-center w-8 h-6">
                                {isPending ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <div className="flex items-center">
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className={`size-6 transition ${isActive
                                                ? 'text-white hover:text-white hover:bg-blue-700'
                                                : 'hover:bg-gray-200 dark:hover:bg-gray-600'
                                                }`}
                                            onClick={(e) => {
                                                e.preventDefault();
                                                e.stopPropagation();
                                                handleStartEditing(chat);
                                            }}
                                        >
                                            <Pencil className="w-3 h-3" />
                                        </Button>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className={`size-6 transition ${isActive
                                                ? 'text-white hover:text-white hover:bg-blue-700'
                                                : 'hover:bg-gray-200 dark:hover:bg-gray-600'
                                                }`}
                                            onClick={(e) => {
                                                e.preventDefault();
                                                e.stopPropagation();
                                                remove(chat.id);
                                            }}
                                        >
                                            <Trash2 className="w-3 h-3" />
                                        </Button>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                );
            })}
        </SidebarGroup>
    );
}
