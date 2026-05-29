from sqlalchemy import select, text
from app.TablePakage.model.parameter_schema import ParameterSchema
# from app.FormulaPakage.utils.calculated_utils import OPERATIONS, PRIORITY
# from app.FormulaPakage.model.selected_file import SelectedFile
# from app.FormulaPakage.model.constants import Constants
# from app.FormulaPakage.model.user_input import UserInput
from app.TablePakage.utils.router_utils import to_sql_name_kir
from .code_mode import CodeParametr, ALLOWED_FUNCTIONS
from fastapi import HTTPException

from collections import deque
from sqlalchemy import text

# async def check_operation(condition_param, condition_value, condition_operator):
#     """
#     Функция проверяет соблюдаются ли условия в Condition
#     """
#     try:
#         condition_param = float(condition_param)
#         condition_value = float(condition_value)
#         check_operation = OPERATIONS[condition_operator](condition_param, condition_value)
#         if check_operation:
#             return True
#         return False
#     except ValueError: # если значение не конвертируется в число, то это операции со строками
#         check_operation = OPERATIONS[condition_operator](condition_param, condition_value)
#         if check_operation:
#             return True
#         return False

# async def calculated_params(note_params_info, db, user_params):
#     try:
#         priority_nodes = {op: [] for op in PRIORITY}
#         for item in note_params_info:
#             op = item['operation']
#             if op in priority_nodes:
#                 priority_nodes[op].append(item)

#         # Преобразуем пустые списки в None
#         priority_nodes = {k: (v if v else None) for k, v in priority_nodes.items()}
#         if not priority_nodes[PRIORITY[0]]:
#             raise HTTPException(status_code=500, detail="Отсутствует стартовый параметр в Calculated")

#         start_value_id = priority_nodes[PRIORITY[0]][0]['parameter_id']
#         priority_nodes.pop(PRIORITY[0])
#         param_start_stmt =  await db.execute(select(ParameterSchema.name).where(ParameterSchema.id == start_value_id))
#         param_start = param_start_stmt.scalar()

#         param_start_res = [item['response_value'] for item in user_params if item['name'] == param_start][0]
#         # param_start_res = user_params[param_start] if param_start in user_params and isinstance(user_params[param_start], str) and "Введите" not in user_params[param_start] else None
        
#         if not param_start_res or "Введите" in param_start_res:
#             param_start_kir = to_sql_name_kir(param_start)
#             return f"Введите значения для параметра {param_start_kir!r}"

#         result_param = float(param_start_res)

#         for queue_operation, value in priority_nodes.items(): 
#             if not value:
#                 continue
#             for val in value:
#                 param_val_stmt =  await db.execute(select(ParameterSchema.name).where(ParameterSchema.id == val['parameter_id']))
#                 param_val = param_val_stmt.scalar()
#                 # param_val_res = user_params[param_val] if param_start in user_params and isinstance(user_params[param_val], str) and "Введите" not in user_params[param_val] else None
#                 param_val_res = [item['response_value'] for item in user_params if item['name'] == param_val][0]
#                 if not param_val_res or "Введите" in param_val_res:
#                     param_start_kir = to_sql_name_kir(param_val)
#                     return f"Введите значения для параметра {param_start_kir!r}"
#                 result_param = OPERATIONS[queue_operation](result_param, float(param_val_res))


#         return result_param
#     except Exception as e:
#         print(f'Ошибка в функции calculated_params: ', str(e))
#         return None

# async def code_params(note_params_info, db, user_params, param_info, select_formula_params):
async def code_params(db, func_name, param_info, user_params, select_formula_params, column_to_param=[]):
    #тут надо вызвать нужную функцию по её названию из БД
    cp_class = CodeParametr()
    # cp_method_name = param_info.field_of_view
    cp_method = getattr(cp_class, func_name)

    return await cp_method(user_params, param_info, select_formula_params, db, column_to_param)

# async def condition_params(param_info, db, params):
#     if not param_info['condition_param_id'] or not param_info['condition_value']:
#         return None
    
#     param_1_stmt =  await db.execute(select(ParameterSchema.name).where(ParameterSchema.id == param_info['condition_param_id']))
#     param_1 = param_1_stmt.scalar()
#     # param_1_res = params[param_1] if param_1 in params and isinstance(params[param_1], str) and "Введите" not in params[param_1] else None
#     param_1_res = [item['response_value'] for item in params if item['name'] == param_1][0]
    
#     if not param_1_res or "Введите" in param_1_res:
#         param_1_kir = to_sql_name_kir(param_1)
#         return f"Введите значения для параметра {param_1_kir!r}"
    
#     if param_info['result_value_type']:
#         the_resulting_param_stmt =  await db.execute(select(ParameterSchema).where(ParameterSchema.id == int(param_info['result_value'])))
#         the_resulting_param = the_resulting_param_stmt.scalar() 
#         if not the_resulting_param:
#             return None
        
#         is_confirm = await check_operation(condition_param=param_1_res, condition_value=param_info['condition_value'], condition_operator=param_info['condition_operator'])
#         if not is_confirm:
#             return None
#         if the_resulting_param.field_of_view['selected_file']:
#             the_resulting_param_value_stmt = await db.execute(select(SelectedFile.file_url).whsere(SelectedFile.result_param_id == int(param_info['result_value'])))
#             the_resulting_param_value = the_resulting_param_value_stmt.scalar()
#             return the_resulting_param_value
#         elif the_resulting_param.field_of_view['user_input']:
#             the_resulting_param_value_stmt = await db.execute(select(UserInput.min_value, UserInput.max_value).where(UserInput.result_param_id == int(param_info['result_value'])))
#             the_resulting_param_value = the_resulting_param_value_stmt.fetchall()
#             min_value, max_value = the_resulting_param_value[0]
#             return [min_value, max_value]

#     else:
#         is_confirm = await check_operation(condition_param=param_1_res, condition_value=param_info['condition_value'], condition_operator=param_info['condition_operator'])
        
#         if not is_confirm:
#             return None
        
#         return param_info['result_value']

# async def user_input_params(param_info, db, params):
#     if param_info['min_value'] is None or param_info['max_value'] is None:
#         return None
#     return [str(param_info['min_value']), str(param_info['max_value'])]
    

FUNCS_FOR_FIELD_OF_VIEW = {"codeparam" : code_params} # "calculated": calculated_params, "conditions": condition_params, "user_input": user_input_params, 


async def get_dependencies_for_param(param, db):
    """
    Возвращает список имён параметров, от которых зависит данный параметр.
    """
    # Определяем тип формулы по field_of_view
    table_name = next(key for key, value in param.field_of_view.items() if value)
    deps_ids = []

    if table_name == 'calculated':
        # Запрос к таблице calculated
        stmt = text("SELECT parameter_id FROM calculated WHERE result_param_id = :id")
        res = await db.execute(stmt, {'id': param.id})
        row = res.first()
        if row:
            if row.parameter_id:
                deps_ids.append(row.parameter_id)

    elif table_name == 'conditions':
        # Запрос к таблице conditions
        stmt = text("SELECT condition_param_id FROM conditions WHERE result_param_id = :id")
        res = await db.execute(stmt, {'id': param.id})
        row = res.first()
        if row and row.condition_param_id:
            deps_ids.append(row.condition_param_id)

    # Преобразуем id в имена параметров
    if deps_ids:
        # Загружаем имена всех упомянутых параметров одним запросом
        param_names_stmt = select(ParameterSchema.name).where(ParameterSchema.id.in_(deps_ids))
        param_names = await db.execute(param_names_stmt)
        return param_names.scalars().all()
    return []

async def search_formula(db, params, table_name_params, select_formula_params=[], full_info=[], column_to_param=[]):
    # 1. Получаем все формульные параметры (кроме selected_file)
    stmt_formula_params = select(ParameterSchema).where(ParameterSchema.type == 'Formula', ParameterSchema.table_name == table_name_params ) #! искать формульные параметры только для этого же продукта
    res = await db.execute(stmt_formula_params)
    all_formula_params = res.scalars().all()
    
    # Отфильтровываем selected_file, т.к. они не вычисляются, а просто возвращают файл
    # Отфильтровываем constants, т.к. они не вычисляются, а просто возвращают константу
    formula_params = []
    for param in all_formula_params:
        # async def code_params(db, func_name, param_info, user_params, select_formula_params):
        func_name = param.field_of_view
        
        res = await code_params(db, func_name, param, params, select_formula_params, column_to_param) #####!ВОЗМОЖНО ТАК НЕЛЬЗЯ - table_formula_params[0]
        if res is not None:
            if "total_change" in res:
                # print(res["total_change"][-1])
                params = res["total_change"]
                # return params
                continue

            # item = {
            #     'id': param.id,
            #     'name': param.name,
            #     'description': param.description,
            #     'visibility': param.visibility,
            #     'required_type': param.required_type
            # }
            
            if "error" in res:
                params.append(res)
            #     item['error'] = res["error"]
            # if "result" in res:
            #     item['result'] = res["result"]
            # params.append(item)
    return params