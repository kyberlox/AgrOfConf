import { type IRequestCostumerData } from "@/assets/interfaces/ICreateRequest"

export const customers = [
    { title: 'Запрос', hidden: false },
    { title: 'Заказчик', hidden: false },
    { title: 'Проектная организация', hidden: true },
    { title: 'Конечный заказчик', hidden: true }
]

// Поля запроса
export const requestFields: IRequestCostumerData[] = [
    {
        title: 'Назначение',
        type: 'select',
        options: [
            'проект(бюджет)',
            'реконструкция(ремонт)',
            'новый объект строительства',
        ]
    },
    {
        title: 'Объект строительства',
        type: 'input'
    },
    {
        title: 'Срок',
        type: 'date'
    },
    {
        title: 'Тип процедуры',
        type: 'select',
        options: [
            'запрос от клиента',
            'конкурс на  электронной площадке(тендер)',
            'запрос для закрытого конкурса',
            'другое'
        ]
    },
    {
        title: 'Описание',
        type: 'textarea'
    }
]

// Поля заказчика
export const customerFields: IRequestCostumerData[] = [
    { title: 'Название', type: 'input' },
    { title: 'ИНН', type: 'input' },
    { title: 'Юридический адрес', type: 'input' },
    { title: 'Фактический адрес', type: 'input' },
    { title: 'Международный адрес', type: 'input' },
    { title: 'Телефон', type: 'input' },
    { title: 'Сайт', type: 'input' },
    { title: 'Контакты', type: 'input' }
]
