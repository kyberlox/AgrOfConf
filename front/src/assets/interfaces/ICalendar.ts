export interface ICalendarWeek {
    days: {
        text: number | string;
        value: Date;
        current: boolean;
        classData: Record<string, boolean>;
    }[];
}
