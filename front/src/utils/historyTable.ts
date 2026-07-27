import { type IHistory } from '@/assets/interfaces/IHistory.ts';

export const headerComparsion = {
    'Шифр ОЛ': 'id',
    'ОЛ №': 'document_number',
    'Статус': 'status',
    'Док. №': 'document_number',
    'Готовность': 'status',
    'Наименование': 'product_name',
    'Шт.': 'quantity',
    'Комментарий:': 'Комментарий',
    'Созд.': 'date_search',
    'Ред.': 'date_search',
    'Отпр.': 'date_search',
} as const;

export const formatResultToHistory = (historyData: IHistory[]) => {
    const result: string[][] = [];
    historyData.forEach(historyElement => {
        const res: string[] = []
        Object.keys(headerComparsion).forEach(header => {
            const target = historyElement[headerComparsion[header as keyof typeof headerComparsion]];
            res.push(target as string)
        })
        result.push(res)
    })
    return result
}