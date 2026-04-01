'use client';

import React, { useState, useEffect } from 'react';
import Joyride, { CallBackProps, STATUS } from 'react-joyride';
import { TourTooltip } from '@/components/agent/AppTour/TourTooltip';
import { getJoyrideStyles } from '@/components/agent/AppTour/styles';
import { steps } from '@/components/agent/AppTour/steps';

export function AppTour() {
    const [run, setRun] = useState(false);

    useEffect(() => {
        const hasSeenTour = localStorage.getItem('hasSeenAppTour');
        if (!hasSeenTour) {
            setRun(true);
        }
    }, []);

    const handleJoyrideCallback = (data: CallBackProps) => {
        const { status } = data;
        const finishedStatuses: string[] = [STATUS.FINISHED, STATUS.SKIPPED];

        if (finishedStatuses.includes(status)) {
            setRun(false);
            localStorage.setItem('hasSeenAppTour', 'true');
        }
    };

    return (
        <Joyride
            steps={steps}
            run={run}
            continuous={true}
            showProgress={true}
            showSkipButton={true}
            callback={handleJoyrideCallback}
            scrollOffset={100}
            styles={getJoyrideStyles()}
            tooltipComponent={TourTooltip}
        />
    );
}
