type IHistoryParam = Record<string, string>;

export interface IHistory {
    [key: string]: string | number | IHistoryParam;
    total_count: number;
}

export interface IHistoryResponse {
    data: IHistory[];
    total_count: number;
}

export interface ICellClicked {
    value: string;
    column: {
        colId: string;
    };
}
