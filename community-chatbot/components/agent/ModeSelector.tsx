'use client';

import { ModeButton } from '@/components/agent/ModeSelector/ModeButton';
import { integrationModes } from '@/lib/constants/chat';

export function ModeSelector() {
    return (
        <div id="mode-selector" className="bg-white dark:bg-gray-800 p-4 dark:border-gray-700 border-b">
            <div className="gap-2 sm:gap-3 grid grid-cols-2 lg:grid-cols-4">
                {integrationModes.map((mode) => (
                    <ModeButton key={mode.id} mode={mode} />
                ))}
            </div>
        </div>
    );
}
