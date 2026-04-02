'use client';

import Image from 'next/image';
import { usePathname } from 'next/navigation';

import {
    Card, CardContent, CardDescription,
    CardHeader, CardTitle,
} from '@/components/ui/card';
import { integrationModes } from '@/lib/constants/chat';

export default function AgentMode() {
    const pathname = usePathname();
    const mode = pathname.split('/')[1];

    const modeDetails = integrationModes.find((m) => m.id === mode);
    if (!modeDetails) return null;

    return (
        <div className="flex justify-center items-center bg-gradient-to-br from-gray-50 dark:from-gray-900 via-blue-50/30 dark:via-blue-950/20 to-purple-50/20 dark:to-purple-950/10 px-6 py-10 h-full">
            <Card className="group relative border-gray-200/60 dark:border-gray-700/60 w-full max-w-sm overflow-hidden hover:scale-[1.02] transition-all duration-300">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-purple-500/5 to-pink-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                <CardHeader className="relative flex flex-col items-center space-y-4 pb-4">
                    <div className="flex justify-center items-center bg-gradient-to-br from-blue-50 to-purple-50 shadow-lg p-3 rounded-full ring-2 ring-blue-100/50 dark:group-hover:ring-blue-800/50 dark:ring-blue-900/50 group-hover:ring-4 group-hover:ring-blue-200/50 w-24 h-24 overflow-hidden group-hover:scale-110 transition-all duration-300">
                        <Image
                            src={modeDetails.image}
                            alt={modeDetails.name}
                            width={96}
                            height={96}
                            className="w-full h-full object-contain group-hover:rotate-6 transition-transform duration-300"
                        />
                    </div>
                    <CardTitle className="dark:group-hover:text-blue-400 group-hover:text-blue-600 text-2xl transition-colors duration-300">
                        {modeDetails.name}
                    </CardTitle>
                </CardHeader>
                <CardContent className="relative text-center">
                    <CardDescription className="text-sm leading-relaxed">
                        {modeDetails.description}
                    </CardDescription>
                </CardContent>
            </Card>
        </div>
    );
}