import '../controller.d.ts';

type FilePath = string;

type Unit = {
    readFile: (path: FilePath) => string;
    writeFile: (path: FilePath, text: string) => void;
    appendFile: (path: FilePath, text: string) => void;
    deleteFile: (path: FilePath) => void;
    execute: (args: string[]) => void;
};

declare global {
    interface Units {
        os: Unit;
    }
}
