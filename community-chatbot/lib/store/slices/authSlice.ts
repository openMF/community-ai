import { getAuth, onAuthStateChanged, User } from 'firebase/auth';
import { StateCreator } from 'zustand';

import { createDefaultChats, fetchChatsForUser } from '@/lib/firestore';

export interface AuthSlice {
	currentUser: User | null;
	initAuth: () => () => void;
	fetchChats: () => Promise<void>;
}

export const createAuthSlice: StateCreator<AuthSlice & any, [], [], AuthSlice> = (set, get) => ({
	currentUser: null,

	initAuth: () => {
		const auth = getAuth();
		const unsubscribe = onAuthStateChanged(auth, (user) => {
			set({ currentUser: user });
			if (user) {
				get().fetchChats();
			} else {
				set({ chatHistory: [], messages: [], activeConversationIds: {}, currentUser: null });
			}
		});
		return unsubscribe;
	},

	fetchChats: async () => {
		const { currentUser} = get();
		if (!currentUser) return;

		try {
			let chatsData = await fetchChatsForUser(currentUser.uid);

			if (chatsData.length === 0) {
				chatsData = await createDefaultChats(currentUser.uid);
			}

			const newActiveConversationIds = chatsData.reduce((acc, chat) => {
				if (!acc[chat.mode] || chat.active) {
					acc[chat.mode] = chat.id;
				}
				return acc;
			}, {} as Record<string, string>);

			set({
				chatHistory: chatsData,
				activeConversationIds: newActiveConversationIds
			});

			const { selectedMode } = get();
			const activeConvId = newActiveConversationIds[selectedMode];
			const activeConversation = chatsData.find((c) => c.id === activeConvId);
			if (activeConversation) {
				set({ messages: activeConversation.messages || [] });
			} else if (chatsData.length > 0) {
				// If no active conversation for the current mode, but chats exist, switch to the first one
				const firstChatInMode = chatsData.find(chat => chat.mode === selectedMode);
				if (firstChatInMode) {
					get().switchConversation(firstChatInMode.id);
				} else {
					// If no chats for the current mode, clear messages
					set({ messages: [] });
				}
			} else {
				// No chats at all, clear messages
				set({ messages: [] });
			}

		} catch (err) {
			console.error("Failed loading chats from Firestore:", err);
		}
	},
});
