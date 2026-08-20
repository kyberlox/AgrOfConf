export interface IStatisticBlock {
    name: string,
    title: string,
    value: number | null,
    icon: object,
    undertext: string,
    comparsion: number | null
}

export interface IStatisticResponse {
    "month": {
        "current": number,
        "previous": number,
        "diff": number
    },
    "day": {
        "current": number,
        "previous": number,
        "diff": number
    },
    "year": {
        "current": number,
        "previous": number,
        "diff": number
    },
    "total": number
}

export interface IMonthMetricInner {
    current: number,
    previous: number,
    diff: number
}

export interface IMonthMetric {
    day: IMonthMetricInner,
    month: IMonthMetricInner,
    year: IMonthMetricInner,
    total: number
}

export interface IYearMetric {
    current_year: { [key: string]: number },
    previous_year: { [key: string]: number }
}