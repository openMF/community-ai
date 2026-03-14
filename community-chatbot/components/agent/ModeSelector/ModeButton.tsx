'use client';

import Image from 'next/image';
import { usePathname, useRouter } from 'next/navigation';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface ModeButtonProps {
    mode: {
        id: string;
        name: string;
        image: string;
    };
}

export function ModeButton({ mode }: ModeButtonProps) {
    const router = useRouter();
    const pathname = usePathname();
    const currentMode = pathname.split('/')[1];
    const isActive = currentMode === mode.id;

    const handleClick = () => {
        if (!isActive) router.push(`/${mode.id}`);
    };

    return (
        <Button
            id={isActive ? 'active-assistant' : undefined}
            onClick={handleClick}
            variant={isActive ? 'default' : 'outline'}
            className={cn(
                'flex sm:flex-row flex-col justify-center sm:justify-start items-center sm:items-start gap-1 sm:gap-2 p-2 sm:p-3 w-full h-auto sm:text-left text-center transition-all',
                isActive && 'bg-blue-600 hover:bg-blue-700'
            )}
        >
            <div className="bg-white p-1 rounded-full">
                <Image
                    src={mode.image}
                    alt={mode.name}
                    width={20}
                    height={20}
                    className="rounded-full"
                />
            </div>
            <span className="max-w-[80px] sm:max-w-none font-medium text-xs sm:text-sm truncate">
                {mode.name}
            </span>
        </Button>
    );
}
