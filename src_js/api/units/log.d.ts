import '../controller.d.ts';

type Level = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';

type Unit = {
    log: (level: Level, msg: string) => void;
    debug: (msg: string) => void;
    info: (msg: string) => void;
    warning: (msg: string) => void;
    error: (msg: string) => void;
};

declare global {
    interface Units {
        log: Unit;
    }
}
