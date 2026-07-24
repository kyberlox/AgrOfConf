KEY_MAPPING = {
    # Основные параметры заказчика
    "Email Заказчика": "email_customer",
    "Адрес Заказчика": "address_customer",
    "Должность Заказчика": "position_customer",
    "Организация Заказчика": "organization_customer",
    "Телефон Заказчика": "phone_customer",
    "ФИО Заказчика": "fio_customer",
    
    # Параметры продукта
    "Маркировка": "marking",
    "Чертеж": "drawing_url",
    "Комментарий": "comment",
    
    # Технические характеристики
    "Высота H, мм": "height_h",
    "Коэф. расхода газа α1": "flow_coefficient_gas",
    "Коэф. расхода жидкости α2": "flow_coefficient_liquid",
    "Масса, кг": "weight_kg",
    "Площадь седла, мм²": "seat_area",
    "Строительная длина L1, мм": "construction_length_l1",
    "Строительная длина L2, мм": "construction_length_l2",
    
    # Материалы
    "Материал корпуса": "body_material",
    "Материал золотника и седла": "spool_seat_material",
    "Материал крышки, колпака и направляющей втулки": "cover_cap_bushing_material",
    
    # Давление и диаметры
    "Номинальное давление входное, кгс/см²": "nominal_pressure_inlet",
    "Номинальное давление выходное, кгс/см²": "nominal_pressure_outlet",
    "Номинальный диаметр входной, мм": "nominal_diameter_inlet",
    "Номинальный диаметр выходной, мм": "nominal_diameter_outlet",
    
    # Температура
    "Температура рабочей среды максимальная, °C": "max_working_temperature",
    "Температура рабочей среды минимальная, °C": "min_working_temperature",
    
    # Типы и исполнения
    "Тип конструкции": "design_type",
    "Тип присоединения к трубопроводу": "connection_type",
    "Тип уплотнения": "seal_type",
    "Тип уплотнения затвора": "gate_seal_type",
    "Фланцевое исполнение": "flange_version",
    "Климатическое исполнение": "climate_version",
    "По способу сброса рабочей среды": "discharge_method",
    
    # Дополнительные опции
    "Испытания": "tests",
    "Покраска": "painting",
    "Устройство принудительного открытия": "forced_opening_device",
    "painting": "has_cof",
    "Наличие ЗИП": "has_spare_parts",  # Оставлен для совместимости, если понадобится
    
    # Цены
    "Цена /шт. руб без НДС": "price_without_vat",
    "Цена /шт. руб с НДС 22%": "price_with_vat",
    
    # Параметры исполнителя
    "дата": "date",
    "номер_запроса": "request_number",
    "адрес_исполнителя": "executor_address",
    "телефон_исполнителя": "executor_phone",
    "email_исполнителя": "executor_email",
    "фио_исполнителя": "executor_fio",
    "должность_исполнителя": "executor_position",
    
    # Служебные
    "id": "id",
    "Проектная организация": "design_organization",
}