type IHistoryParam = Record<string, string>;

export interface IHistory {
    [key: string]: string | IHistoryParam
}