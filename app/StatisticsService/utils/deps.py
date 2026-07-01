from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import text


async def build_statistic_data(db, user_id: int, product_id: int):
    stmt = await db.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id})
    user_info_row = stmt.fetchone()
    stmt = await db.execute(text("SELECT * FROM products WHERE id = :id"), {"id": product_id})
    product_info_row = stmt.fetchone()
    product_info = dict(product_info_row._mapping)
    user_info = dict(user_info_row._mapping)
    date_search = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    result = {
        "product_id": product_info.get("id"),
        "user_id": user_info.get("id"),
        "date_search": date_search,
        # Product fields
        "product_name": product_info.get("name", ""),
        "product_description": product_info.get("description", ""),
        "product_manufacturer": product_info.get("manufacturer", ""),
        "product_image_url": product_info.get("image_url", ""),
        "product_image_url": product_info.get("image_url", ""),

        # User fields (с переименованием и конкатенацией ФИО)
        "user_uuid": user_info.get("uuid", ""),
        "user_fio": f"{user_info.get('last_name', '')} {user_info.get('name', '')} {user_info.get('second_name', '')}".strip(),
        "user_email": user_info.get("email", ""),
        "user_directorate": user_info.get("directorate") or "",
        "user_work_position": user_info.get("work_position") or "",
        "user_office": str(user_info.get("office", "")),
        "user_department": user_info.get("department") or "",
        "user_work_city": user_info.get("work_city") or "",
        "user_work_phone": user_info.get("work_phone") or "",
    }

    return result
