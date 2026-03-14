'use client';

import React from 'react';
import { TooltipRenderProps } from 'react-joyride';
import { X, ArrowRight, ArrowLeft, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function TourTooltip({
    index,
    step,
    backProps,
    primaryProps,
    skipProps,
    isLastStep,
}: TooltipRenderProps) {
    return (
        <div className="bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800 shadow-2xl p-6 border rounded-2xl w-full max-w-[400px] transition-all overflow-hidden relative">
            {/* Header / Step Progress */}
            <div className="flex justify-between items-center mb-4">
                <span className="bg-blue-100 dark:bg-blue-900/50 px-2 py-0.5 rounded text-blue-600 dark:text-blue-400 text-xs font-bold uppercase tracking-wider">
                    Step {index + 1}
                </span>
                <button
                    {...skipProps}
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
                    title="Skip Tour"
                >
                    <X className="size-5" />
                </button>
            </div>

            {/* Content Area */}
            <div className="mb-8">
                {step.content}
            </div>

            {/* Footer / Navigation */}
            <div className="flex items-center gap-3">
                {index > 0 && (
                    <Button
                        {...backProps}
                        variant="ghost"
                        size="sm"
                        className="text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
                    >
                        <ArrowLeft className="mr-2 size-4" />
                        Back
                    </Button>
                )}

                <div className="flex-1" />

                <Button
                    {...primaryProps}
                    size="sm"
                    className="bg-blue-600 hover:bg-blue-700 text-white font-semibold min-w-[100px]"
                >
                    {isLastStep ? (
                        <>
                            Get Started
                            <Check className="ml-2 size-4" />
                        </>
                    ) : (
                        <>
                            Continue
                            <ArrowRight className="ml-2 size-4" />
                        </>
                    )}
                </Button>
            </div>
        </div>
    );
}
