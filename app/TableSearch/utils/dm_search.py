from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.TablePakage.utils.router_utils import to_sql_name_lat


async def rebuild_dm(
    db: AsyncSession,
    product_id: int,
):
    await db.execute(
        text("SELECT pg_advisory_lock(:pid)"),
        {"pid": product_id}
    )

    try:
        dm_table = f"dm_product_{product_id}"

        # удаляем старую витрину
        await db.execute(
            text(f'DROP TABLE IF EXISTS "{dm_table}"')
        )

        # получаем все параметры продукта
        result = await db.execute(text("""
            SELECT
                name,
                transliterated_name,
                table_name
            FROM parameter_schemas
            WHERE product_id = :pid
              AND type = 'Table'
              AND table_name IS NOT NULL
        """), {
            "pid": product_id
        })

        params = result.mappings().all()

        # если параметров нет — создаём пустую dm
        if not params:
            await db.execute(text(f"""
                CREATE TABLE "{dm_table}" (
                    param_name TEXT,
                    values TEXT[],
                    matched_rows INTEGER
                )
            """))

        else:
            union_queries = []

            for row in params:
                param_name = row["name"]
                col = row["transliterated_name"]
                table_name = row["table_name"]

                union_queries.append(f"""
                    SELECT
                        '{param_name}'::text AS param_name,
                        array_agg(DISTINCT "{col}")
                            FILTER (WHERE "{col}" IS NOT NULL) AS values,
                        COUNT(*) AS matched_rows
                    FROM "{table_name}"
                """)

            final_sql = f"""
                CREATE TABLE "{dm_table}" AS
                {" UNION ALL ".join(union_queries)}
            """

            await db.execute(text(final_sql))

        # registry
        await db.execute(text("""
            INSERT INTO datamart_registry (
                product_id,
                dm_table_name,
                is_dirty,
                updated_at
            )
            VALUES (
                :pid,
                :dm_table_name,
                FALSE,
                now()
            )
            ON CONFLICT (product_id)
            DO UPDATE
            SET is_dirty = FALSE,
                updated_at = now()
        """), {
            "pid": product_id,
            "dm_table_name": dm_table
        })

        await db.commit()

    finally:
        await db.execute(
            text("SELECT pg_advisory_unlock(:pid)"),
            {"pid": product_id}
        )

async def ensure_dm_exists(
    db: AsyncSession,
    product_id: int,
):
    registry = await db.execute(text("""
        SELECT is_dirty
        FROM datamart_registry
        WHERE product_id = :pid
    """), {"pid": product_id})

    row = registry.mappings().first()

    if not row:
        await rebuild_dm(db, product_id)
        return

    if row["is_dirty"]:
        await rebuild_dm(db, product_id)


# def build_dm_sql(
#     table_name: str,
#     schema_params: list[str],
#     product_id: int,
# ) -> str:
#     unions = []
#
#     for param_name in schema_params:
#         col = to_sql_name_lat(param_name)
#
#         unions.append(f"""
#             SELECT
#                 '{param_name}'::text AS param_name,
#                 array_agg(DISTINCT "{col}") FILTER (WHERE "{col}" IS NOT NULL) AS values,
#                 COUNT(*) AS matched_rows
#             FROM "{table_name}"
#         """)
#
#     union_sql = "\nUNION ALL\n".join(unions)
#
#     return f"""
#         DROP TABLE IF EXISTS dm_product_{product_id};
#
#         CREATE TABLE dm_product_{product_id} AS
#         {union_sql};
#     """


async def get_full_search_from_dm(
        db: AsyncSession,
        product_id: int,
) -> tuple[dict, int]:
    result = await db.execute(text(f"""
        SELECT param_name, values, matched_rows
        FROM dm_product_{product_id}
    """))

    rows = result.mappings().all()

    parameters = {}
    matched_rows_list = []

    for row in rows:
        param_name = row["param_name"]
        values = row["values"]
        matched_rows = row["matched_rows"] or 0

        matched_rows_list.append(matched_rows)

        if not values:
            continue

        if param_name not in parameters:
            parameters[param_name] = set()

        for value in values:
            parameters[param_name].add(str(value))

    parameters = {
        param_name: sorted(values)
        for param_name, values in parameters.items()
    }

    max_rows = max(matched_rows_list) if matched_rows_list else 0

    return parameters, max_rows