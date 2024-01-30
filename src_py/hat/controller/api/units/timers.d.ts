import type { Trigger } from '../controller.d.ts';

type TimerName = string;

type TimerDuration = number;  // ms

type Timestamp = number;  // ms

interface TimerTrigger extends Trigger {
    type: 'timers/timer';
    name: TimerName;
    data: Timestamp;
}

type Unit = {
    start: (name: TimerName) => void;
    stop: (name: TimerName) => void;
};

declare global {
    interface Units {
        timers: Unit;
    }
}
