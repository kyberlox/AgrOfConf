import { type IHistory } from "@/assets/interfaces/IHistory.ts";

export const headerComparsionReq = {
    "Запрос №": "request_num",
    Статус: "status",
    "Ол(шт.)": "ol_count",
    Заказчик: "customer",
    ПО: "organization",
    Наименование: "product_name",
    Описание: "description",
    "Комментарий:": "commentary",
    "Созд.": "created_at",
    "Ред.": "edited_at",
    "Отпр.": "dispatched_at",
    Конечный: "end_customer",
} as const;

export const headerComparsionOl = {
    "Шифр ОЛ": "id",
    "ОЛ №": "document_number",
    Статус: "status",
    Готовность: "status",
    Наименование: "product_name",
    "Шт.": "quantity",
    "Комментарий:": "Комментарий",
    "Созд.": "date_search",
    "Ред.": "date_search",
    "Отпр.": "date_search",
} as const;

export const formatResultToHistory = (historyData: { data: IHistory[] }, type: "ol" | "req") => {
    const headerComparsion = type == "ol" ? headerComparsionOl : headerComparsionReq;
    const result: string[][] = [];
    if (!historyData?.data.length) return [];
    historyData.data.forEach((historyElement) => {
        const res: string[] = [];
        Object.keys(headerComparsion).forEach((header) => {
            const typedHeader = header as keyof typeof headerComparsion;
            const typedComparsion = headerComparsion[typedHeader] as unknown as keyof typeof historyElement;
            const target = historyElement[typedComparsion];
            res.push(target as string);
        });
        result.push(res);
    });
    return result;
};
