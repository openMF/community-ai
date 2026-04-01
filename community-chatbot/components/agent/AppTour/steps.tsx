import { Step } from "react-joyride";

export const steps: Step[] = [
    {
        target: 'body',
        content: (
            <div className="text-left">
                <h3 className="font-bold text-lg mb-2">Welcome</h3>
                <p className="text-sm opacity-80">
                    Welcome to your workspace. This app uses different assistants for different tasks. Let’s take a quick tour.
                </p>
            </div>
        ),
        placement: 'center',
        disableBeacon: true,
    },
    {
        target: '#mode-selector',
        content: (
            <div className="text-left">
                <h3 className="font-bold text-lg mb-2">Assistants</h3>
                <p className="text-sm opacity-80">
                    Select an assistant based on what you want to do. Each assistant is designed for a specific type of work.
                </p>
            </div>
        ),
        placement: 'bottom',
    },
    {
        target: '#active-assistant',
        content: (
            <div className="text-left">
                <h3 className="font-bold text-lg mb-2">Current Assistant</h3>
                <p className="text-sm opacity-80">
                    Only one assistant can be active at a time. All actions and responses follow this selection.
                </p>
            </div>
        ),
        placement: 'bottom',
    },
    {
        target: '#chat-history',
        content: (
            <div className="text-left">
                <h3 className="font-bold text-lg mb-2">Conversation History</h3>
                <p className="text-sm opacity-80">
                    This shows past conversations for the selected assistant. Each assistant has its own history.
                </p>
            </div>
        ),
        placement: 'right',
    },
    {
        target: '#new-chat-button',
        content: (
            <div className="text-left">
                <h3 className="font-bold text-lg mb-2">New Chat</h3>
                <p className="text-sm opacity-80">
                    Start a new conversation here. The chat will belong to the currently selected assistant.
                </p>
            </div>
        ),
        placement: 'bottom',
    },
    {
        target: 'body',
        content: (
            <div className="text-left">
                <h3 className="font-bold text-lg mb-2">All Set</h3>
                <p className="text-sm opacity-80">
                    You’re ready to begin. Choose an assistant and start your first conversation.
                </p>
            </div>
        ),
        placement: 'center',
    },
];
