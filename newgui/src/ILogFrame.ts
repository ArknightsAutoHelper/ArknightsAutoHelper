export interface ILogFrame {
    addLogRecord: (record: ILogRecord) => void;
    clearLog: () => void;
    setAutoScroll: (value: boolean) => void;
    setScrollBackLimit: (limit: number) => void;
    setShowDebug: (show: boolean) => void;
    setDarkMode: (dark: boolean) => void;
}

export interface ILogRecord {
    time: Date;
    level: string;
    message: string;
    id: string;
}
