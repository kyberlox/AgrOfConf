type IHistoryParam = Record<string, string>;

export interface IHistory {
    [key: string]: string | number | IHistoryParam,
    total_count: number
}