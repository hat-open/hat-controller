import type { Trigger, JsonData } from '../controller.d.ts';

interface CustomTrigger extends Trigger {
    type: 'triggers/custom';
}

type Delay = number;  // ms

type Unit = {
    getCurrent: () => Trigger | null;
    raise: (name: string, data?: JsonData, delay?: Delay) => void;
};

declare global {
    interface Units {
        triggers: Unit;
    }
}
