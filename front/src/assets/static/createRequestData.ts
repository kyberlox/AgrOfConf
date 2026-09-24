import { type IRequestCostumerData, type ICustomer } from "@/assets/interfaces/ICreateRequest";

export const customers: ICustomer[] = [
    { title: "Запрос", hidden: false, id: "request" },
    { title: "Заказчик", hidden: false, id: "customer" },
    { title: "Проектная организация", hidden: true, id: "organization" },
    { title: "Конечный заказчик", hidden: true, id: "end_customer" },
];

// Поля запроса
export const requestFields: IRequestCostumerData[] = [
    {
        id: "request_purpose",
        title: "Назначение",
        type: "select",
        options: ["проект(бюджет)", "реконструкция(ремонт)", "новый объект строительства"],
    },
    {
        id: "construction_project",
        title: "Объект строительства",
        type: "input",
    },
    {
        id: "tkp_term",
        title: "Срок ТКП",
        type: "date",
    },
    {
        id: "delivery_time",
        title: "Срок доставки",
        type: "date",
    },
    {
        id: "procedure_type",
        title: "Тип процедуры",
        type: "select",
        options: [
            "запрос от клиента",
            "конкурс на  электронной площадке(тендер)",
            "запрос для закрытого конкурса",
            "другое",
        ],
    },
    {
        id: "description",
        title: "Описание",
        type: "textarea",
    },
];

// Поля заказчика
export const customerFields: IRequestCostumerData[] = [
    { id: "organization", title: "Название", type: "input" },
    { id: "inn", title: "ИНН", type: "input" },
    { id: "registered_address", title: "Юридический адрес", type: "input" },
    { id: "address", title: "Фактический адрес", type: "input" },
    { id: "international_address", title: "Международный адрес", type: "input" },
    { id: "telephone", title: "Телефон", type: "input" },
    { id: "website", title: "Сайт", type: "input" },
    { id: "email", title: "Эл. почта", type: "input" },
    { id: "", title: "Контакты", type: "input" },
];
