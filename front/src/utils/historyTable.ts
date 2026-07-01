import { type IHistory } from '@/assets/interfaces/IHistory.ts';

export const headerComparsion = {
    'Шифр ОЛ': 'id',
    'ОЛ №': 'document_number',
    'Статус': 'status',
    'Документ №': 'document_number',
    'Готовность': 'ready',
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
            res.push(String(historyElement[headerComparsion[header as keyof typeof headerComparsion]]) || '?')
        })
        result.push(res)
    })
    return result
}