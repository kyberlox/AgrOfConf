from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from math import sqrt
from app.TablePakage.utils.router_utils import to_sql_name_lat, to_sql_name_kir
from math import sqrt, log, exp, pi, log10
import math
#функция выводит значение параметра по названию
# def get_param_by_name(param_name, selection_result):
#     #найти параметр
#     for param in selection_result:
#         if param["name"] == param_name:
#             #нет ли ошибки
#             if "error" in param:
#                 return False
#             #вывести
#             return param
#     #или None
#     return None

class CodeParametr:

    # def __init__(self, product_id, param_id):
    #     self.product_id = product_id
    #     self.param = param_id

    #функция выводит значение параметра по названию
    def _get_param_by_name(self, param_name, selection_result):
        #найти параметр
        for param in selection_result:
            if "debug" in param: 
                continue #пропускаем дебаг-параметр -1, который нужен для проверки, что все работает правильно. "debug": True
            
            if param["name"] == param_name:
                #нет ли ошибки
                if "error" in param:
                    return False
                #вывести
                return param
        #или None
        return None

    def _set_params(self, selection_result, param_id, param_name, param_description="", param_type="list", visibility=True, response_value=None, all_values=[], error=None, sort=None):
        new_param = {
                "id" : param_id,
                "name" : param_name,
                "description" : param_description,
                "visibility" : visibility,
                'required_type': param_type
            }
        if param_type == "list" or param_type == "select-input":
            new_param["all_values"] = all_values

        if response_value:
            new_param["response_value"] = response_value
        if error:
            new_param["error"] = error
        if sort is not None:
            new_param["sort"] = sort

        selection_result.append(new_param)

        return selection_result
    
    def _linear_interpolation(x1, y1, x2, y2, x):
        """
        Функция для линейной интерполяции.

        :param x1: x-координата первой точки
        :param y1: y-координата первой точки
        :param x2: x-координата второй точки
        :param y2: y-координата второй точки
        :param x: x-координата точки, для которой нужно найти y
        :return: интерполированное значение y
        """
        if x1 == x2:
            raise ValueError("x1 и x2 не должны быть равны, чтобы избежать деления на ноль.")

        # Вычисляем y по формуле линейной интерполяции
        y = y1 + (x - x1) * (y2 - y1) / (x2 - x1)
        return y

    async def make_mixture(self, selection_result, param_info, select_formula_params, db, column_to_param=[]):
        """
        алгоритм подбора смеси
        """
        # print(selection_result)
        # print(param_info)
        # print(select_formula_params)
        #чтобы не падала ошибка табличного подбора
        debug_param = {
            "id" : -1,
            "debug" : False,
            'visibility': False
        }
        res = [debug_param]

        #как понять на каком я этапе?
        naydeno = False
        is_mixture = False
        got_envs = False
        got_climate = False
        got_type = False
        got_T = False

        counter_for_id = param_info.id
        counter_for_sort = 1
        # поиск смеси среди выбранных значений
        if select_formula_params != []:
            for param_name, value in select_formula_params.items():
                if param_name == "Смесь":
                    naydeno = True
                    if value == "Да":
                        res = self._set_params(res, counter_for_id, "Смесь", param_description=param_info.description, all_values=["Да", "Нет"], response_value="Да", sort=counter_for_sort)
                        is_mixture = True

                    elif value == "Нет":
                        res = self._set_params(selection_result, counter_for_id, "Смесь", param_description=param_info.description, all_values=["Да", "Нет"], response_value="Нет", sort=counter_for_sort)
                        
        if not naydeno:
            res = self._set_params(res, 1, "Смесь", all_values=["Да", "Нет"], sort=1)
        
        if is_mixture:
            counter_for_id += 1
            counter_for_sort += 1
            #список ВСЕХ сред
            param = self._get_param_by_name("Название рабочей среды", selection_result)
            all_values = param["all_values"]
            envs_param = select_formula_params.get("Состав смеси")
            
            if not envs_param:
                description = "Нужно выбрать состав смеси из списка доступных сред и указать их мольные доли (%)"
                res = self._set_params(res, counter_for_id, "Состав смеси", param_description=description, all_values=all_values, sort=counter_for_sort, param_type="select-input")

            elif envs_param:
                #проверить правильность
                envs = envs_param
                #сумма мольных долей
                r_sum = sum(list(env.values())[0] for env in envs)
                
                #хватает ли сред для смеси
                if envs == [] or len(envs) == 1:
                    description = "Нужно выбрать состав смеси из списка доступных сред и указать их мольные доли (%)"
                    error = "Смесь не может состоять менее чем из двух сред!"
                    res = self._set_params(res, counter_for_id, "Состав смеси", param_description=description, all_values=all_values, sort=counter_for_sort, param_type="select-input", response_value=envs, error=error)

                #праивльная ли сумма их долей?
                elif r_sum != 100:
                    description = "Нужно выбрать состав смеси из списка доступных сред и указать их мольные доли (%)"
                    error = f"Сумма мольных долей сред смеси должна составлять 100%, а не {r_sum}%"
                    res = self._set_params(res, counter_for_id, "Состав смеси", param_description=description, all_values=all_values, sort=counter_for_sort, param_type="select-input", response_value=envs, error=error)
                
                #если всё правильно
                else:
                    description = "Нужно выбрать состав смеси из списка доступных сред и указать их мольные доли (%)"
                    res = self._set_params(res, counter_for_id, "Состав смеси", param_description=description, all_values=all_values, sort=counter_for_sort, param_type="select-input", response_value=envs)
                    got_envs = True

        #Если это не смесь
        elif naydeno and is_mixture is False:
            envs = select_formula_params.get("Название рабочей среды")
            if envs:
                # got_envs = True
                got_type = True
                # got_climate = True
        #климатика
        if got_envs:
            counter_for_id += 1
            counter_for_sort += 1
            #список ВСЕХ климатик
            is_climate = self._get_param_by_name("Климатическое исполнение по ГОСТ 15150-69", selection_result)
            error_climate = None 
            climate = None
            if not is_climate:
                error_climate = "Невозможно подобрать климатическое исполнение для таких сред"
            else:
                climate = is_climate['all_values']
            type_param = select_formula_params.get("Климатическое исполнение по ГОСТ 15150-69")
            
            climate_values = type_param
            #если нет
            if climate_values is None and climate:
                res = self._set_params(res, counter_for_id, "Климатическое исполнение по ГОСТ 15150-69", all_values=climate, sort=counter_for_sort)
            elif not climate:
                res = self._set_params(res, counter_for_id, "Климатическое исполнение по ГОСТ 15150-69", all_values=[], sort=counter_for_sort, error=error_climate)
            else:
                res = self._set_params(res, counter_for_id, "Климатическое исполнение по ГОСТ 15150-69", all_values=climate, sort=counter_for_sort, response_value=climate_values)
                got_climate = True
        
        #Тип клапана
        # type_val = None
        if got_climate:
            counter_for_id += 1
            counter_for_sort += 1
            #список ВСЕХ климатик
            all_type_names = self._get_param_by_name("Тип клапана", selection_result)["all_values"]
            # type_param = self._get_param_by_name("Тип предохранительного клапана", select_formula_params)
            type_param = select_formula_params.get("Тип клапана")
            
            type_val = type_param # is not None

            #если нет
            if type_val is None:
                res = self._set_params(res, counter_for_id, "Тип клапана", all_values=all_type_names, sort=counter_for_sort)

            #валидация нужна
            elif type_val not in all_type_names:
                error = "Надо выбрать один из предложеннных вариантов"
                res = self._set_params(res, counter_for_id, "Тип клапана", all_values=all_type_names, sort=counter_for_sort, error=error, response_value=type_val)

            else:
                res = self._set_params(res, counter_for_id, "Тип клапана", all_values=all_type_names, sort=counter_for_sort, response_value=type_val)
                got_type = True
        
        #Температура
        if got_type:
            counter_for_id += 1
            counter_for_sort += 1
            # задана пользователем?
            # T_param  = self._get_param_by_name("Температура рабочей среды", select_formula_params)
            T_param  = select_formula_params.get("Температура рабочей среды")
            T = int(T_param) if T_param else None

            description = "Ввведите значение температуры рабочей среды (°C)"
            required_type = "user_input"
            response_value = T

            type_param = select_formula_params.get("Тип клапана")
            
            type_val = type_param
            #если нет
            if T is None:
                res = self._set_params(res, counter_for_id, "Температура рабочей среды", param_description=description, sort=counter_for_sort, param_type=required_type) #all_values=all_type_names, 
            else:
                if type_val:
                    #валидировать:
                    if (type_val == "Пружинный (В)" and (T < -60 or T > 600) ) or (type_val == "Пилотный (П)" and (T < -60 or T > 250) ):
                        error = "Температура должна быть в диапазоне от -60°С до 600°С для пружинных и от -60°С до 250°С для пилотных клапанов"
                        res = self._set_params(res, counter_for_id, "Температура рабочей среды", param_description=description, sort=counter_for_sort, param_type=required_type, response_value=response_value, error=error) #all_values=all_type_names, 
                    
                    else:
                        res = self._set_params(res, counter_for_id, "Температура рабочей среды", param_description=description, sort=counter_for_sort, param_type=required_type, response_value=response_value) #all_values=all_type_names, 
                        got_T = True
                else:
                    error = "Заполните Тип клапана"
                    res = self._set_params(res, counter_for_id, "Температура рабочей среды", param_description=description, sort=counter_for_sort, param_type=required_type, response_value=response_value, error=error) #all_values=all_type_names, 
                    
        ################# РАСЧЕТ #################
        if got_T:
            counter_for_id += 1
            counter_for_sort += 1
            #ключи === названия колонок БД
            searching_table_name = "pktable_1"

            #чтобы проще было заполнять
            # all_columns_names = await db.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = \'{searching_table_name}\';"))
            # rows_all_columns_names = [row.column_name for row in all_columns_names]
            # print("Список колонок таблицы: ", rows_all_columns_names)
        

            # env_keys = {
            #     "name" : "nazvanie_rabochej_sredy",
            #     "environment" : "agregatnoe_sostojanie",
            #     "molecular_weight" : "molekuljarnaja_massa",
            #     "density" : "plotnost_zhidkosti",
            #     # "density_ns": "",
            #     "material" : "material",
            #     "viscosity" : "vjazkost_pa_s",
            #     "isobaric_capacity" : "udel_naja_izobarnaja_teploemkost_kdzh_kg_k",
            #     "molar_mass" : "moljarnaja_massa",
            #     "isochoric_capacity" : "udel_naja_izohornaja_teploemkost_kdzh_kg_k",
            #     "adiabatic_index" : "pokazatel_adiabaty",
            #     "compressibility_factor" : "faktor_szhimaemosti",
            # }
            env_keys = [
                "nazvanie_rabochej_sredy", "agregatnoe_sostojanie",
                "molekuljarnaja_massa", "plotnost_zhidkosti",
                "material", "vjazkost_pa_s",
                "udel_naja_izobarnaja_teploemkost_kdzh_kg_k",
                "moljarnaja_massa",
                "udel_naja_izohornaja_teploemkost_kdzh_kg_k",
                "pokazatel_adiabaty", "faktor_szhimaemosti",
            ]
            #собрать список параметров сред
            envs_json = []
            env_type = set()

            # env_name_colunm = env_keys["name"]
            env_name_colunm = "nazvanie_rabochej_sredy"
            if isinstance(envs, list):
                for env in envs:
                    env_name = list(env.keys())[0]
                    r = env[env_name] / 100
                    ###################### собрать sql запрос ##############################
                    env_params_sql = "SELECT "
                    # for keys in env_keys.keys():
                    for colunm_name in env_keys:
                        # colunm_name = env_keys[keys]
                        env_params_sql += colunm_name + ", "
                    env_params_sql = env_params_sql[:-2]
                    env_params_sql += f" FROM {searching_table_name} WHERE {env_name_colunm} = \'{env_name}\';"
                    # print(env_params_sql)
                    sql_result = await db.execute( text(env_params_sql) )
                    env_result = sql_result.mappings().first() 
                    if not env_result:
                        continue
                    # print(env_result, "ЧЕ получили перед ошибкой")
                    ###################### обработать его в json ###########################
                    env_json = {
                        "name" : env_result.nazvanie_rabochej_sredy,
                        "r" : r,
                        "environment" : env_result.agregatnoe_sostojanie,
                        "molekuljarnaja_massa" : env_result.molekuljarnaja_massa,
                        "plotnost_zhidkosti" : env_result.plotnost_zhidkosti,
                        "material" : env_result.material,
                        "vjazkost_pa_s" : env_result.vjazkost_pa_s,
                        "isobaric_capacity" : env_result.udel_naja_izobarnaja_teploemkost_kdzh_kg_k,
                        "moljarnaja_massa" : env_result.moljarnaja_massa,
                        "isochoric_capacity" : env_result.udel_naja_izohornaja_teploemkost_kdzh_kg_k,
                        "pokazatel_adiabaty" : env_result.pokazatel_adiabaty,
                        "compressibility_factor" : env_result.faktor_szhimaemosti,
                    }
                    #возможные типы состава сред
                    env_type.add(env_json["environment"])

                    #значения для ключей среды
                    envs_json.append(env_json)
            #Если это не смесь
            elif isinstance(envs, str):
                env_name = envs
                r = 1
                ###################### собрать sql запрос ##############################
                env_params_sql = "SELECT "
                # for keys in env_keys.keys():
                for colunm_name in env_keys:
                    # colunm_name = env_keys[keys]
                    env_params_sql += colunm_name + ", "
                env_params_sql = env_params_sql[:-2]
                env_params_sql += f" FROM {searching_table_name} WHERE {env_name_colunm} = \'{env_name}\';"
                # print(env_params_sql)
                sql_result = await db.execute( text(env_params_sql) )
                env_result = sql_result.mappings().first() 
                if not env_result:
                    print(env_result, "ЧЕ получили перед ошибкой, строка 333")
                ###################### обработать его в json ###########################
                env_json = {
                    "name" : env_result.nazvanie_rabochej_sredy,
                    "r" : r,
                    "environment" : env_result.agregatnoe_sostojanie,
                    "molekuljarnaja_massa" : env_result.molekuljarnaja_massa,
                    "plotnost_zhidkosti" : env_result.plotnost_zhidkosti,
                    "material" : env_result.material,
                    "vjazkost_pa_s" : env_result.vjazkost_pa_s,
                    "isobaric_capacity" : env_result.udel_naja_izobarnaja_teploemkost_kdzh_kg_k,
                    "moljarnaja_massa" : env_result.moljarnaja_massa,
                    "isochoric_capacity" : env_result.udel_naja_izohornaja_teploemkost_kdzh_kg_k,
                    "pokazatel_adiabaty" : env_result.pokazatel_adiabaty,
                    "compressibility_factor" : env_result.faktor_szhimaemosti,
                }
                #возможные типы состава сред
                env_type.add(env_json["environment"])

                #значения для ключей среды
                envs_json.append(env_json)


            result = {
                "nazvanie_rabochej_sredy" : "",
                "agregatnoe_sostojanie" : "",
                "molekuljarnaja_massa" : 0,
                "plotnost_zhidkosti" : 0,
                # "density_ns": 0,
                "material" : "",
                "vjazkost_pa_s" : 0,
                "udel_naja_izobarnaja_teploemkost_kdzh_kg_k" : 0,
                "moljarnaja_massa" : 0,
                # "udel_naja_izohornaja_teploemkost_kdzh_kg_k" : 0,
                "pokazatel_adiabaty" : 0,
                "faktor_szhimaemosti" : 1,
            }
            r_max = 0
            if len(env_type) == 1:
                env_type_name = f"{list(env_type)[0]}" #Однородная смесь - 
                result["agregatnoe_sostojanie"] = env_type_name

                if list(env_type)[0] == "Жидкость":
                    ch_den = 0
                    zn_den = 0
                    pre_viscosity = 0
                    for env in envs_json:
                        r = env["r"]
                        result["nazvanie_rabochej_sredy"] += f"{env['name']}:{r}% " 
                        result["molekuljarnaja_massa"] += float(env["molekuljarnaja_massa"]) * r
                        ch_den += float(env["plotnost_zhidkosti"]) * r
                        zn_den += r
                        pre_viscosity += log10(float(env["vjazkost_pa_s"])) * r


                    result["plotnost_zhidkosti"] = ch_den/zn_den
                    result["vjazkost_pa_s"] = 10**(pre_viscosity)

                elif list(env_type)[0] == "Газ": #если среда - газ
                    viscosity_сh = 0
                    viscosity_zn = 0
                    pre_M = 0
                    adiabatic_index = 0
                    adiabatic_index_zn = 0
                    for env in envs_json:
                        r = env["r"]
                        result["nazvanie_rabochej_sredy"] += f"{env['name']}:{r*100}% "
                        M_i = float(env["moljarnaja_massa"])
                        u_i = float(env["vjazkost_pa_s"])
                        pre_M += M_i * r
                        viscosity_сh += u_i * r * sqrt(M_i)
                        viscosity_zn += r * sqrt(M_i)
                        adiabatic_index += float(env['pokazatel_adiabaty']) * r
                        #!!!!! env['pokazatel_adiabaty'] приходит 46113, а должен 1.4
                        # плотность при н.у.
                        result["plotnost_zhidkosti"] += (M_i * r)
                    result["moljarnaja_massa"] = pre_M #/100
                    result["vjazkost_pa_s"] = viscosity_сh / viscosity_zn
                    result["pokazatel_adiabaty"] = adiabatic_index

                        # плотность при н.у.
                    result["plotnost_zhidkosti"] = result["plotnost_zhidkosti"] / 22.4
            else:
                result["agregatnoe_sostojanie"] = "Неоднородная смесь"
                density_ch = 0
                density_zn = 0
                pre_u = 0
                for env in envs_json:
                    # print(env, "че такое?")
                    r = env["r"]
                    result["nazvanie_rabochej_sredy"] += f"{env['name']}:{r}% "

                    # pre_viscosity += log10(env["viscosity"]) * r

                    if env["environment"] == "Газ":
                        M = float(env["moljarnaja_massa"])
                        density_ch += (float(env["moljarnaja_massa"]) / 22.4) * r
                        density_zn += r
                    elif env["environment"] == "Жидкость":
                        M = float(env["molekuljarnaja_massa"])
                        density_ch += float(env["plotnost_zhidkosti"]) * r
                        density_zn += r

                    pre_u += r * float(env["vjazkost_pa_s"]) * M

                    if r > r_max:
                        # Плотность несущей среды при нормальных условиях
                        r_max = r
                        # result["density_ns"] = density_ch / density_zn

                #рабочая плотность
                result["plotnost_zhidkosti"] = density_ch / density_zn
                result["vjazkost_pa_s"] = pre_u

                material = []
            
            material = []
            for env in envs_json:
                if ( env['name'] == 'Сероводород' and env["r"] < 0.06 ) and result["agregatnoe_sostojanie"] == "Смесь":
                    material.append(f"25Л")
                else:
                    material.append(env['material'])

            ln = 0
            for mat in material:
                if len(mat) > ln:
                    ln = len(mat)
                    result["material"] = mat

            #если климатика => то материал
            climate = select_formula_params.get('Климатическое исполнение по ГОСТ 15150-69')
            if climate and ((climate == "ХЛ1") or (climate == "УХЛ1")) and (result["material"] == "25Л"):
                if T < 350.0:
                    result["material"] = "20ГЛ"
                elif T >= 350.0 and climate == "ХЛ1":
                    result["material"] = "12Х18Н9ТЛ"


            for param_name, value in result.items():
                if param_name == 'nazvanie_rabochej_sredy': #либо удалить параметр состав смеси
                    continue
                kir_param_name = column_to_param[param_name]
                param_info = [param for param in selection_result if param["name"] == kir_param_name]
                if not param_info:
                    continue
                param_info = param_info[0]
                res = self._set_params(res, counter_for_id, kir_param_name, param_description=param_info["description"], response_value=value, sort=counter_for_sort, param_type='raschet') 
                counter_for_id += 1
                counter_for_sort += 1
            # Поскольку расчет смеси завершился, докидываем
            # параметры из БД для следующего расчета
            for param_db in selection_result:
                # print(param_db['name'], "Какие параметры из БД")
                
                param_info = [param_res for param_res in res if "name" in param_res and param_res["name"] == param_db["name"]] # 'debug' in param_res or 
                if param_info:
                    # print(param_info, 'ЧТО НЕ ПРОШЛО УСЛОВИЕ И ТО ЧТО УЖЕ БЫЛО В РЕЗУЛЬТАТЕ')
                    continue
                
                if param_db["table_name"] in ['table2', 'table3', 'table4', 'table10']:
                    # print(param_db['name'], 'ЧТО ТАБЛИЧНОЕ?')
                    continue
                if param_db['name'] == 'Название рабочей среды' and (select_formula_params.get('Смесь') and select_formula_params.get('Смесь') == 'Да'):
                    # print(123123123) В БУДУЩЕМ ПОДУМАТЬ КАК УБРАТЬ НАЗВАНИЕ РАБОЧЕЙ СРЕДЫ
                    continue
                param_db['id'] = counter_for_id
                param_db['sort'] = counter_for_sort
                counter_for_id += 1
                counter_for_sort += 1
                res.append(param_db)

        return {"total_change" : res}

    async def _searchT2(self, T, Pn, db):
        #print(f"T2: {Pn}")
        #найти все подходящие строки их DNS и P1 - больше искомых)
        query = """
            SELECT * FROM table2 
            WHERE t::float >= :T_val
            AND pn::float >= :Pn_val
        """
        params = {"T_val": T, "Pn_val": Pn}
        stmt = await db.execute(text(query), params) 
        request = stmt.fetchall()
        # request = db.query("table2").filter(Table2.t >= T, Table2.pn >= Pn).all()

        if request == None or len(request) == 0:
            return False
        ans = False

        #найти самый подходящий - MIN по DNS и P1
        minT = request[0].t
        minPn = request[0].pn
        for example in request:
            if (example.t <= minT) and (example.pn <= minPn):
                minT = example.t
                minPn = example.pn
                ans = {
                    "ID" : example.id,  
                    "T" : example.t, 
                    "Pn" : example.pn * 10, 
                    "PN" : example.p
                }
        #print(ans)
        return ans
    
    async def _searchT10(self, T, Pn, db):
        #print(f"T10: {Pn}")
        #найти все подходящие строки их DNS и P1 - больше искомых
        # request = db.query(Table10).filter(Table10.T >= T, Table10.Pn >= Pn).all()
        query = """
            SELECT * FROM table10 
            WHERE t10::float >= :T_val 
            AND pn10::float >= :Pn_val
        """
        params = {"T_val": T, "Pn_val": Pn}
        stmt = await db.execute(text(query), params) 
        request = stmt.fetchall()

        if request == None or len(request) == 0:
            return False
        ans = False

        #найти самы подходящий - MIN по DNS и P1
        minT = request[0].t10
        minPn = request[0].pn10
        for example in request:
            if (example.t10 <= minT) and (example.pn10 <= minPn):
                minT = example.t10
                minPn = example.pn10
                ans = {
                    "ID" : example.id,  
                    "T" : example.t10, 
                    "Pn" : example.pn10, 
                    "PN" : example.p10
                }
        #print(ans)
        return ans

    async def _searchParams(self, db, DNS, Pn, PN, valve_type):
        #найти все подходящие строки их DNS и P1 - больше искомых
        # request = db.query(Params).filter(Params.DNS >= DNS, Params.PN == PN, Params.valve_type == valve_type).all()
        # print(DNS, type(DNS), PN, type(PN), valve_type, 123123123)
        query = """
            SELECT * FROM table3 
            WHERE dns3::float >= :DNS_val 
            AND pn3::float = :Pn_val
            AND tip_klapana = :valve_type
        """
        params = {"DNS_val": DNS, "Pn_val": PN, "valve_type": valve_type}
        stmt = await db.execute(text(query), params) 
        request = stmt.all()

        if request == None or request == []:
            return False
        ans = False
        #найти самый подходящий - MIN по DNS и P1
        minDNS = request[0].dns3
        #minP1 = request[0].P1
        minPN = request[0].pn3
        ##print("###")
        for example in request:

            #print(example.id, example.DNS, example.valve_type, example.DN, example.PN)
            # print(example.id, example.dns3, example.tip_klapana, example.dn3, example.pn3, "ЧТО ПОЛУЧАЕМ")
            try:
                Pn1 = str(example.pnd3).split("...")[0]
                Pn2 = str(example.pnd3).split("...")[1]
                #print(Pn1, Pn2)
                #print(f"example.DNS <= minDNS {example.DNS <= minDNS} example.PN == minPN {example.PN == minPN} float(Pn1) <= Pn <= float(Pn2) {float(Pn1)} {Pn} {float(Pn2)} {float(Pn1) <= Pn <= float(Pn2)}")
                if (float(example.dns3) <= float(minDNS))  and (float(example.pn3) == float(minPN)) and (float(Pn1) <= Pn <= float(Pn2)):
                    minDNS = example.dns3
                    #minP1 = example.P1
                    minPN = example.pn3
                    ans = {
                        "ID" : example.id,
                        "DNS" : example.dns3,
                        "Pnd" : example.pnd3,
                        "DN" : example.dn3,
                        "PN" : example.pn3,
                        "spring_material" : example.material_pruzhiny,
                        "spring_number" : example.nomer_pruzhiny,
                        "valve_type" : valve_type
                    }
                elif (Pn <= float(Pn2)) and (Pn <= 4) and (float(example.dns3) <= float(minDNS))  and (float(example.pn3) == float(minPN)):
                    minDNS = example.dns3
                    # minP1 = example.P1
                    minPN = example.pn3
                    ans = {
                        "ID" : example.id,
                        "DNS" : example.dns3,
                        "Pnd" : example.pnd3,
                        "DN" : example.dn3,
                        "PN" : example.pn3,
                        "spring_material" : example.material_pruzhiny,
                        "spring_number" : example.nomer_pruzhiny,
                        "valve_type" : valve_type
                    }
            except:
                print("###")
                print(example.id)
                print(example.Pnd)
                print("###")
        #print("###")
        #print(ans)

        return ans 

    async def _get_by_mark(self, db, mark, DN, PN):
        mark = float(mark[2:5])
        query = """
            SELECT * FROM table4 
            WHERE mark4::float = :mark
            AND dn4::float = :dn
            AND pn4::float = :pn
        """
        params = {"mark": mark, "dn": DN, "pn": PN}
        stmt = await db.execute(text(query), params) 
        request = stmt.first()
        # request = db.query(pakingParams).filter(pakingParams.mark == mark, pakingParams.DN == DN, pakingParams.PN == PN).first()
        # print(mark, DN, PN, 12341243)
        if request is None:
            return None, None
        else:

            M = None
            S = None
            # print(request)
            if request.m4 is not None:
                M = request.m4
            if request.s4 is not None:
                S = request.s4
            # print(M, S)
            return (M, S)

    async def raschet(self, selection_result, param_info, select_formula_params, db, column_to_param=[]):
        from copy import deepcopy
        #Флаги
        force_open = None # "Устройство принудительного открытия"
        Pn = None # "Давление настройки"
        Gab = None # "Максимальный аварийный расход жидкости и газа"
        N = None # "Количество параллельно установленных и одновременно работающих клапанов (шт)"
        pre_Kc = None # Мембранно-предохранительное устройство
        Pp = None # Противодавление статическое
        Pp_din = None # Противодавление динамическое
        if not select_formula_params:
            return {"total_change" : selection_result}
        
        selection_result.pop(0)
        res = deepcopy(selection_result)

        last_sort = 0
        
        sorted_params = sorted([item for item in selection_result if 'sort' in item], key=lambda x: x['sort'])
        last_param = sorted_params[-1]
        counter_for_id = last_param['id']
        counter_for_sort = last_param['sort']
        #Ищем Устройство принудительного открытия
        # for param_name, value in select_formula_params.items():
        if select_formula_params.get("Устройство принудительного открытия"):
            
            #ищем данные параметра
            param_info = [param for param in selection_result if param["name"] == "Устройство принудительного открытия"]
            if not param_info:
                # res = self._set_params(selection_result, param_info['id'], param_name, param_description=param_info['description'], all_values=["Да", "Нет"], response_value=value, sort=param_info['sort'])
                return {'error': 'Не найден параметр в БД - Устройство принудительного открытия'}
            force_open = select_formula_params.get("Устройство принудительного открытия")
            # param_info = param_info[0]
            # res = self._set_params(res, param_info['id'], param_name, param_description=param_info['description'], all_values=["Да", "Нет"], response_value=value, sort=param_info['sort'])
            # last_sort = param_info['sort']
        if select_formula_params.get("Давление настройки") and force_open:
            # if not value:
            #     continue
            Pn = float(select_formula_params.get("Давление настройки"))
            # last_sort += 1
            counter_for_id += 1
            counter_for_sort += 1
            if Pn > 16 or Pn < 0:
                res = self._set_params(res, counter_for_id, "Давление настройки", param_type='user_input', param_description="", response_value=Pn, sort=counter_for_sort, error="Давление настройки не может быть меньше 0 и больше 16")
                # continue
            else:
                res = self._set_params(res, counter_for_id, "Давление настройки", param_type='user_input', param_description="", response_value=Pn, sort=counter_for_sort)
        if select_formula_params.get("Максимальный аварийный расход жидкости и газа") and force_open:
            # if not value:
            #     continue
            Gab = float(select_formula_params.get("Максимальный аварийный расход жидкости и газа"))
            # last_sort += 1
            counter_for_id += 1
            counter_for_sort += 1
            if Gab < 0:
                res = self._set_params(res, counter_for_id, "Максимальный аварийный расход жидкости и газа", param_type='user_input', param_description="", response_value=Gab, sort=counter_for_sort, error="Значение не может быть меньше 0")
            else:
                res = self._set_params(res, counter_for_id, "Максимальный аварийный расход жидкости и газа", param_type='user_input', param_description="", response_value=Gab, sort=counter_for_sort)
        if select_formula_params.get("Количество параллельно установленных и одновременно работающих клапанов (шт)") and force_open:
            # if not value:
            #     continue
            N = float(select_formula_params.get("Количество параллельно установленных и одновременно работающих клапанов (шт)"))
            # last_sort += 1
            counter_for_id += 1
            counter_for_sort += 1
            if N < 0:
                res = self._set_params(res, counter_for_id, "Количество параллельно установленных и одновременно работающих клапанов (шт)", param_type='user_input', param_description="", response_value=N, sort=counter_for_sort, error="Значение не может быть меньше 0")
            else:
                res = self._set_params(res, counter_for_id, "Количество параллельно установленных и одновременно работающих клапанов (шт)", param_type='user_input', param_description="", response_value=N, sort=counter_for_sort)
        if select_formula_params.get("Мембранно-предохранительное устройство") and force_open:
            pre_Kc = select_formula_params.get("Мембранно-предохранительное устройство")
            # last_sort += 1
            counter_for_id += 1
            counter_for_sort += 1
            res = self._set_params(res, counter_for_id, "Мембранно-предохранительное устройство", param_description="", all_values=["Да", "Нет"], response_value=pre_Kc, sort=counter_for_sort)
        if select_formula_params.get("Противодавление статическое") and Pn:
            # if not value:
            #     continue
            # last_sort += 1
            counter_for_id += 1
            counter_for_sort += 1
            Pp = float(select_formula_params.get("Противодавление статическое"))
            if Pp > Pn * 0.7 or Pp < 0:
                res = self._set_params(res, counter_for_id, "Противодавление статическое", param_type='user_input', param_description="", response_value=Pp, sort=counter_for_sort, error="Значение не может быть больше 70% давления настройки и меньше 0")
            else:
                res = self._set_params(res, counter_for_id, "Противодавление статическое", param_type='user_input', param_description="", response_value=Pp, sort=counter_for_sort)
        if select_formula_params.get("Противодавление динамическое") and Pn:
            # if not value:
            #     continue
            # last_sort += 1
            counter_for_id += 1
            counter_for_sort += 1
            Pp_din = float(select_formula_params.get("Противодавление динамическое"))
            
            if Pp_din > Pn * 0.7 or Pp_din < 0:
                res = self._set_params(res, counter_for_id, "Противодавление динамическое", param_type='user_input', param_description="", response_value=Pp_din, sort=counter_for_sort, error="Значение не может быть больше 70% давления настройки и меньше 0")
            else:
                res = self._set_params(res, counter_for_id, "Противодавление динамическое", param_type='user_input', param_description="", response_value=Pp_din, sort=counter_for_sort)

        #Формируем Устройство принудительного открытия
        if not force_open:
            {"total_change" : res}
        #Формируем Давление настройки
        if not Pn and force_open:
            # last_sort += 1
            counter_for_id += 1
            counter_for_sort += 1
            res = self._set_params(res, counter_for_id, "Давление настройки", param_description="", all_values=[0, 16], sort=counter_for_sort, param_type="user_input")
        #Формируем Максимальный аварийный расход жидкости и газа
        if not Gab and force_open:
            # last_sort += 1
            counter_for_id += 1
            counter_for_sort += 1
            res = self._set_params(res, counter_for_id, "Максимальный аварийный расход жидкости и газа", param_description="", all_values=[0, 10 ** 100], sort=counter_for_sort, param_type="user_input")
        #Формируем Количество параллельно установленных и одновременно работающих клапанов (шт)
        if not N and force_open:
            # last_sort += 1
            counter_for_id += 1
            counter_for_sort += 1
            res = self._set_params(res, counter_for_id, "Количество параллельно установленных и одновременно работающих клапанов (шт)", param_description="", all_values=[0, 10 ** 100], sort=counter_for_sort, param_type="user_input")
        #Формируем Мембранно-предохранительное устройство
        if not pre_Kc and force_open:
            # last_sort += 1
            counter_for_id += 1
            counter_for_sort += 1
            res = self._set_params(res, counter_for_id, "Мембранно-предохранительное устройство", param_description="", all_values=["Да", "Нет"], sort=counter_for_sort)
        #Формируем Противодавление статическое
        if not Pp and Pn:
            # last_sort += 1
            counter_for_id += 1
            counter_for_sort += 1
            res = self._set_params(res, counter_for_id, "Противодавление статическое", param_description="", all_values=[0, Pn * 0.7], sort=counter_for_sort, param_type="user_input")
        #Формируем Противодавление динамическое
        if not Pp_din and Pn:
            # last_sort += 1
            counter_for_id += 1
            counter_for_sort += 1
            res = self._set_params(res, counter_for_id, "Противодавление динамическое", param_description="", all_values=[0, Pn * 0.7], sort=counter_for_sort, param_type="user_input")
        
        #Если не все заполнено, возвращаем массив параметров для заполнения
        is_exist = [force_open, Pn, Gab, N, pre_Kc, Pp, Pp_din]
        if not all(x is not None for x in is_exist):
            return {"total_change" : res}
        
        #Все заполнено, можно выполнять расчет
        P_atm = 0.101320
        R = 8.31446261815324  # Газовая постоянная ( Па / (моль * K))
        u_info = select_formula_params.get("Вязкость (Па*с)")
        u = float(u_info) if u_info else None

        "Климатическое исполнение по ГОСТ 15150-69"
        
        climate = select_formula_params["Климатическое исполнение по ГОСТ 15150-69"]
        model = {
            "М1 (от -40, до 40)": [-40, 40],
            "У1 (от -40, до 40)": [-40, 40],
            "УХЛ1 (от -60, до 40)": [-60, 40],
            "ХЛ1 (от -60, до 40)": [-60, 40]
        }

        T_min, T_max = model[climate]

        T = select_formula_params["Температура рабочей среды"]

        if pre_Kc == 'Да':
            Kc = 0.9
        else:
            Kc = 1
        
        # Давление начала открытия
        # Давление полного открытия
        if Pn <= 0.3:
            Pno = Pn + 0.02
            Ppo = Pn + 0.05
        elif (Pn > 0.3) and (Pn <= 6):
            Pno = 1.07 * Pn
            Ppo = 1.15 * Pn
        elif Pn > 6:
            Pno = 1.05 * Pn
            Ppo = 1.1 * Pn
        else:
            return {"error": f"Невозможно определить давление начала открытия и давление полного открытия, при давлении настройки = {Pn}"}

        #Ищем наше агрегатное состояние (среду)
        environment_inf = [param for param in selection_result if param["name"] == 'Агрегатное состояние']
        molar_mass_info = [param for param in selection_result if param["name"] == 'Молярная масса']
        if "Газ" in environment_inf[0]['response_value']:
            #p1 = dt["density_ns"]  * (Ppo * 273.15) / (0.101325 * (T + 273.15))
            #p1 = dt["density_ns"] * ((Ppo * 100000) / (101325 * 8.14))
            
            ch = molar_mass_info[0]["response_value"] * (Ppo*10 + 1) * 100000
            zn = 8314 * (T + 273.15)
            p1 = ch / zn

            # if  dt["convertGab"]:# и размерность м3/час
            #     # Домножить Gab
            #     Gab *= p1
        else:
            #Ищем плотность
            # density_inf = [param for param in selection_result if param["name"] == 'Плотность жидкости']
            density_inf = select_formula_params.get('Плотность жидкости')
            p1 = int(density_inf) if density_inf else None
        
        #!!!!!!!!!!!!! ОБРАТИТЬ ВНИМАНИЕ
        # dt["density"] = #p1 !!!!!!!!!!!!! ОБРАТИТЬ ВНИМАНИЕ

        # Максимально допустимое давление аварийного сброса;
        P_ab_max = 1.1 * Pno

        # Абсолютное давление до клапана,
        P1 = Ppo + P_atm  # < P_ab_max

        # Абсолютное давление за клапаном при его полном открытии
        P2 = Pp + P_atm  # = P_sbr

        # Отношение абсолютных давлений;
        B = P2 / P1

        if "Газ" in environment_inf[0]['response_value']:
            M = molar_mass_info[0]["response_value"]

            p1 = P1 * 1000 * M / (R * (T + 273.15))

            alpha = 0.8
            # (Д.22)
            if (Ppo / Pn) == 1.1:
                if (Pp / Pno) <= 0.3:
                    Kw = 1
                else:
                    Kw = 1.1027 + 0.4007 * (Pp / Pno) - 2.4577 * (Pp / Pno) ** 2
            # (Д.23)
            elif (Ppo / Pn) == 1.15:
                if (Pp / Pno) <= 0.37:
                    Kw = 1
                else:
                    Kw = 1.2857 - 0.7603 * (Pp / Pno)
            # (Д.24)
            elif ((Ppo / Pn) > 1.2) and ((Pp / Pno) >= 0.5):
                Kw = 1
            # (Д.25)
            elif ((Ppo / Pn) > 1.1) and ((Ppo / Pn) <= 1.15):
                # Kw определяют линейной интерполяцией по (Ppo / Pn) между значениями, полученными по (Д.22) и (Д.23)
                #return {"err": f"Нет возможности расчитать {data_mean['Kw']} для соотношения 1.1 < Ppo / Pn <= 1.15, при {data_mean['Ppo']} = {Ppo} и {data_mean['Pn']} = {Pn} "}

                # (Д.22)
                Ppo_Pn_1 = 1.1
                Kw_1 = 1.1027 + 0.4007 * (Pp / Pno) - 2.4577 * (Pp / Pno) ** 2

                # (Д.23)
                Ppo_Pn_2 = 1.15
                Kw_2 = 1.2857 - 0.7603 * (Pp / Pno)

                Kw = self._linear_interpolation(Ppo_Pn_1, Kw_1, Ppo_Pn_2, Kw_2, Ppo / Pn)

            # (Д.26)
            elif ((Ppo / Pn) > 1.15) and ((Ppo / Pn) <= 1.2):
                # Kw определяют линейной интерполяцией по (Ppo / Pn) между значениями, полученными по (Д.23) и (Д.24)
                #return {"err": f"Нет возможности расчитать {data_mean['Kw']} для соотношения 1.1 < Ppo / Pn <= 1.15, при {data_mean['Ppo']} = {Ppo} и {data_mean['Pn']} = {Pn} "}

                # (Д.23)
                Ppo_Pn_1 = 1.15
                Kw_1 = 1.2857 - 0.7603 * (Pp / Pno)

                # (Д.24)
                Ppo_Pn_2 = 1.21
                Kw_2 = 1

                Kw = self._linear_interpolation(Ppo_Pn_1, Kw_1, Ppo_Pn_2, Kw_2, Ppo / Pn)
        
            n_inf = [param for param in selection_result if param["name"] == 'Показатель адиабаты']
            n = n_inf[0]["response_value"]
            Bkr = (2 / (n + 1)) ** (n / (n - 1))
            # определим режим истечения
            if B <= Bkr:  #
                Kb = 1
                if n == 1:
                    Kp_kr = 0.60653 ** 2
                else:
                    # Kp_kr = n*(Bkr**((n+1)/n)) #на самом деле, тут корень, но его будем извлекать в конце
                    Kp_kr = sqrt((2 * n) / (n + 1)) * (2 / (n + 1)) ** (1 / (n - 1))  # или можно так
            else:  # докритический режим
                Kp_kr = 1
                if n == 1:
                    # print("GHT")
                    Kb = B ** 2 * -2 * exp * log(B)  # на самом деле, тут корень, но его будем извлекать в конце
                else:
                    # print("TNVD", B, n) # на сервере TNVD 0.6396824882086095 1.4 | на локалке TNVD 0.6396824882086095 46113.0
                    Kb = (((n + 1) / (n - 1)) * (B ** (2 / n) - B ** ((n + 1) / n)) * ((n + 1) / 2)) ** 2

            # P1 * p1
            Gideal = Kp_kr * Kb * sqrt(P1 * p1)
            # 1731832127.5731838 1 69021157.59355277 11.10132 56.71167636200972 Че получилось - на локалке
            # 5.212068048661966 1 0.20772392684452992 11.10132 56.71167636200972 Че получилось - на сервере
            if Gideal <= 0:
                return {'error': 'ошибка расчетов, Gideal <= 0 там где среда газ'}
        else:
            #(Д.21)
            alpha = 0.6
            # p1 = dt["density"]
            if (Pp / Pno) <= 1.15:
                Kw = 1
            elif ((Pp / Pno) > 1.15) and ((Pp / Pno) <= 0.25):
                Kw = 0.875 + 1.8333 * (Pp / Pno) - 6.6667 * (Pp / Pno) ** 2
            elif (Pp / Pno) > 0.25:
                Kw = 1.149 - 0.988 * (Pp / Pno)

            Kp = sqrt(2 * (1 - B))  # на самом деле, тут корень, но его будем извлекать в конце
            Gideal = Kp * sqrt(P1 * p1)  # на сервере 5.212068048661966 1 0.20772392684452992 11.10132 56.71167636200972 Че получилось
            if Gideal <= 0:
                return {'error': 'ошибка расчетов, Gideal <= 0 там где среда не газ'}
        
        DN_s = None
        pre_DN = 0
        Kv = 1
        
        while DN_s != pre_DN:

            pre_F = Gab / (3.6 * alpha * Kv * Kw * Kc * Gideal * N)
            if pre_F == 0:
                return {"error": f"Ошибка расчета, pre_F == 0"}
            pre_DN = sqrt((4 * pre_F) / pi)
            Re = (Gideal * p1 * pre_DN) / u  # Gideal
            if (Re >= 1000) and (Re <= 100000):
                Kv = (0.9935 + (2.8780 / Re ** 0.5) + (342.75 / Re ** 1.5)) ** (-1)
            elif (Re < 1000):
                Kv = 0.975 * sqrt(1 / 170 / (Re + 0.98))
            else:
                Kv = 1

            F = Gab / (3.6 * alpha * Kv * Kw * Kc * Gideal * N)
            DN_s = sqrt((4 * F) / pi)
        DN_s = math.ceil(DN_s * 10) / 10
        material_inf = [param for param in selection_result if param["name"] == "Материал"]
        if material_inf[0]['response_value'] == "20ГЛ" or material_inf[0]['response_value'] == "25Л":
            ex = await self._searchT2(T, Pn * 10.197162, db)
        else:
            ex = await self._searchT10(T, Pn * 10.197162, db)
        

        if ex:
            PN = ex["PN"]
        else:
            #Собираем ответ
            #Получаем последний айдишник
            param = self._get_param_by_name("Мембранно-предохранительное устройство", res)
            # counter = param['sort'] + 1 #Счетчик для увеличения порядкового номера
            # last_sort += 1
            counter_for_id += 1
            counter_for_sort += 1
            res = self._set_params(res, counter_for_id, "Номинальное давление", param_type='user-input', sort=counter_for_sort, error="Ошибка расчетов: Нет возможности подобрать PN")
            return {"total_change" : res}

        param = self._get_param_by_name("Тип клапана", selection_result)
        valve_type = param["response_value"][-2]
        example = await self._searchParams(db, float(DN_s), float(Pn) * 10.197162, int(PN), valve_type)
        # print(DN_s, Pn, PN, valve_type, 'ЧЕ ЗАКИДЫВАЕМ')
        # print(example, 'ЧЕ ПОЛУЧИЛИ')


        #Собираем ответ
        #Получаем последний айдишник
        param = self._get_param_by_name("Мембранно-предохранительное устройство", res)
        # last_sort += 1
        counter_for_id += 1
        counter_for_sort += 1#Счетчик для увеличения порядкового номера

        #Минимальная рабочая температура
        res = self._set_params(res, counter_for_id, "Минимальная рабочая температура", param_type='raschet', response_value=T_min, sort=counter_for_sort, visibility=False)
        #Максимальная рабочая температура
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(res, counter_for_id, "Максимальная рабочая температура", param_type='raschet', response_value=T_max, sort=counter_for_sort, visibility=False)
        # counter += 1
        # Давление начала открытия с противодавлением
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(res, counter_for_id, "Давление начала открытия с противодавлением", param_type='raschet', response_value=Pno * 10.197162, sort=counter_for_sort)
        # counter += 1
        # Давление полного открытия с противодавлением
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(res, counter_for_id, "Давление полного открытия с противодавлением", param_type='raschet', response_value=Ppo * 10.197162, sort=counter_for_sort)
        # counter += 1
        # Давление на входе
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(res, counter_for_id, "Давление на входе", param_type='raschet', response_value=P1 * 10.197162, sort=counter_for_sort)
        # counter += 1
        # Давление на выходе
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(res, counter_for_id, "Давление на выходе", param_type='raschet', response_value=P2 * 10.197162, sort=counter_for_sort)
        # counter += 1
        # Коэффициент, учитывающий эффект неполного открытия разгруженных ПК из-за противодавления
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(res, counter_for_id, "Коэффициент, учитывающий эффект неполного открытия разгруженных ПК из-за противодавления", param_type='raschet', response_value=Kw, sort=counter_for_sort)
        # counter += 1
        # Массовая скорость
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(res, counter_for_id, "Массовая скорость", param_type='raschet', response_value=Gideal, sort=counter_for_sort)
        # counter += 1
        # Предварительный Диаметр седла клапана, мм:
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(res, counter_for_id, "Предварительный Диаметр седла клапана, мм:", param_type='raschet', response_value=DN_s, sort=counter_for_sort)
        # counter += 1
        # Предварительный Диаметр седла клапана, мм
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(res, counter_for_id, "Диаметр седла клапана, мм:", param_type='raschet', response_value=float(example['DN']), sort=counter_for_sort)
        # counter += 1
        # Номинальный диаметр седла !f example:
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(res, counter_for_id, "Номинальный диаметр седла", param_type='raschet', response_value=float(example["DNS"]), sort=counter_for_sort)
        # counter += 1
        # Номинальный диаметр !f example:
        # res = self._set_params(res, counter, "Номинальный диаметр", param_type='raschet', response_value=example["DN"], sort=counter)
        # counter += 1
        # Номинальное давление !f example:
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(res, counter_for_id, "Номинальное давление", param_type='raschet', response_value=float(example["PN"]), sort=counter_for_sort)
        # counter += 1
        # Номинальный диаметр на выходе
        DN2 = {
            25.0: 40.0,
            50.0: 80.0,
            80.0: 100.0,
            100.0: 150.0,
            150.0: 200.0,
            200.0: 300.0
        }
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(res, counter_for_id, "Номинальный диаметр на выходе", param_type='raschet', response_value=DN2[int(example["DN"])], sort=counter_for_sort)
        # counter += 1
        # Номинальное давление на выходе
        PN2 = {
            16.0: 6,
            40.0: 16.0,
            63.0: 40.0,
            100.0: 40.0,
            160.0: 40.0,
            250.0: 40.0
        }
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(res, counter_for_id, "Номинальное давление на выходе", param_type='raschet', response_value=PN2[int(example["PN"])], sort=counter_for_sort)
        # counter += 1
        # Площадь седла клапана
        DN_s = int(example["DNS"])
        S = (pi * DN_s**2 )/ 4
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(res, counter_for_id, "Площадь седла клапана", param_type='raschet', response_value=S, sort=counter_for_sort)
        # counter += 1
        # Эффективная площадь седла калапана
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(res, counter_for_id, "Эффективная площадь седла калапана", param_type='raschet', response_value=S * alpha, sort=counter_for_sort)
        # counter += 1
        # Материал пружины
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(res, counter_for_id, "Материал пружины", param_type='raschet', response_value=example["spring_material"], sort=counter_for_sort, visibility=False)
        # counter += 1
        # Номер пружины
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(res, counter_for_id, "Номер пружины", param_type='raschet', response_value=example["spring_number"], sort=counter_for_sort, visibility=False)
        # counter += 1
        # Диапазон давлений настройки
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(res, counter_for_id, "Диапазон давлений настройки", param_type='raschet', response_value=example["Pnd"], sort=counter_for_sort, visibility=False)
        # counter += 1
        
        # Переменное противодавление или необходим сильфон на пружинные ПК по требованию ОЛ
        # Проверка есть ли этот параметр среди выбранных и какое у него значение
        is_need_bellows = select_formula_params.get("Переменное противодавление или необходим сильфон на пружинные ПК по требованию ОЛ")
        if is_need_bellows:
            need_bellows = is_need_bellows
        else:
            need_bellows = None

        if (valve_type == 'В') and (((example["spring_material"] == '51ХФА') and (T > 120)) or ((example["spring_material"] == '50ХФА') and (T > 250))):
            need_bellows = "Да"
        elif valve_type == 'В' and not is_need_bellows:
            need_bellows = None
        else:
            need_bellows = "Нет"
        
        env_names = list()
        cool_env = ["Вода", "Водяной пар", "Воздух", "Азот", "Вода"]
        evil_env = False
        cool = 0
        is_mixture = select_formula_params.get("Состав смеси")
        if is_mixture:
            # Если это смесь, то собираем список компонентов
            
            envs_value = select_formula_params.get("Состав смеси")
            for env in envs_value:
                env_value = list(env.keys())[0]
                if env_value in cool_env:
                    cool += 1
                env_names.append(list(env.keys())[0])
        else:
            env = select_formula_params.get("Название рабочей среды")
            if env in cool_env: 
                cool+=1
            env_names.append(env)
        
        if cool == len(env_names) and (valve_type == 'В') and (((example["spring_material"] == '51ХФА') and (T > 120)) or ((example["spring_material"] == '50ХФА') and (T > 250))):
            evil_env = True

        open_close_type = "закрытого типа"
        if evil_env and T :
            open_close_type = "открытого типа"
            need_bellows = "Нет"
        
        material = None
        if "Сероводород" in env_names and "Хлор" in env_names and PN >= 0.003:
            #молибденовое исполнение
            material = "12Х18Н12М3ТЛ"
            
        # Заполняем need_bellows (list), open_close_type(raschet, тип ПК:, visibility=False), material(raschet, молибденовое исполнение, visibility=False)
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(res, counter_for_id, "Переменное противодавление или необходим сильфон на пружинные ПК по требованию ОЛ", all_values=["Да", "Нет"], response_value=need_bellows, sort=counter_for_sort)
        # counter += 1

        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(res, counter_for_id, "Открытый / Закрытый тип", param_type='raschet', response_value=open_close_type, sort=counter_for_sort)
        # counter += 1

        is_joining_type = select_formula_params.get("Тип присоединения")
        joining_type_values = ["Фланцевое", "Под приварку", "Штуцерно-торцовое", "Муфтовое", "Ниппельное", "Кламповое", "Комбинированное"]
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(res, counter_for_id, "Тип присоединения", all_values=joining_type_values, response_value=is_joining_type, sort=counter_for_sort)
        # counter += 1
        if material:
            counter_for_id += 1
            counter_for_sort += 1
            res = self._set_params(res, counter_for_id, "Молибденовое исполнение", param_type='raschet', response_value=material, sort=counter_for_sort, visibility=False)
            # counter += 1
        
        new_list = []
        for param in res:
            if "table_name" in param and param["table_name"] in ['table2', 'table3', 'table10']:
                # print(param_db['name'], 'ЧТО ТАБЛИЧНОЕ?')
                continue
            new_list.append(param)

        return {"total_change" : new_list}

    async def _find_param_print(self, mark, db, product_id):
        from app.TablePakage.model.product_drawing import ProductDrawing
        from sqlalchemy import select
        # query = """
        #     SELECT file_url FROM product_drawing 
        #     WHERE product_id = :product_id 
        #     AND name = :name
        # """
        # params = {"product_id": product_id, "name": mark}
        # stmt = await db.execute(text(query), params) 
        stmt = select(ProductDrawing).where(ProductDrawing.product_id == product_id) #, ProductDrawing.name.ilike(f'%{mark}%')
        res = await db.execute(stmt)
        request = res.scalars().all()
        # print(request, 'че получили')
        if not request:
            return ""
        for drawing in request:
            print(repr(drawing.name), 'ЧЕ ПОЛУЧАЕМ', repr(mark))
            first_ord_name = drawing.name[0]
            first_ord_mark = mark[0]
            print(ord(first_ord_name), ord(first_ord_mark))
            # print(type(first_ord_name), first_ord_name)
            if drawing.name == mark:
                print('НЕ ДОХОДИТ ДА')
                return drawing.file_url
        
        return None

    async def mark_params(self, selection_result, param_info, select_formula_params, db, column_to_param=[]):
        """
        Параметры которые нужны для расчета:
        - Тип предохранительного клапана Пружинный или Пилотный (B/H) (valve_type)
        - Номинальное давление (PN)
        - Номинальное давление на выходе (PN2)
        - Номинальный диаметр (DN)
        - Температура рабочей среды (T)
        - Тип присоединения (joining_type)
        - Переменное противодавление или необходим сильфон на пружинные ПК по требованию ОЛ (need_bellows)
        - Маркировка (mark)
        """
        sorted_params = sorted([item for item in selection_result if 'sort' in item], key=lambda x: x['sort'])
        last_param = sorted_params[-1]
        counter_for_id = last_param['id']
        counter_for_sort = last_param['sort']

        # Переменная длоя сбора аргументов маркировки
        MARK_ARR = ['X', "X", "X", "X", "X", "X", "X", ""]
        if not select_formula_params:
            return {"total_change" : selection_result}
        valve_type_full = select_formula_params.get("Тип клапана")
        valve_type = None
        if valve_type_full:
            valve_type = valve_type_full.split('(')[-1][0]
        # Проверяем наличие всех параметров
        check_value = self._get_param_by_name("Номинальное давление", selection_result)
        PN = float(check_value['response_value']) if check_value else None
        check_value = self._get_param_by_name("Номинальное давление на выходе", selection_result)
        PN2 = float(check_value['response_value']) if check_value else None
        check_value = self._get_param_by_name("Диаметр седла клапана, мм:", selection_result)
        DN = float(check_value['response_value']) if check_value else None
        check_value = self._get_param_by_name("Температура рабочей среды", selection_result)
        T = float(check_value['response_value']) if check_value and 'response_value' in check_value else None
        check_value = self._get_param_by_name("Давление начала открытия с противодавлением", selection_result)
        Ppo = float(check_value['response_value']) if check_value and 'response_value' in check_value else None
        check_value = self._get_param_by_name("Тип присоединения", selection_result)
        joining_type = check_value['response_value'] if check_value and 'response_value' in check_value else None
        check_value = self._get_param_by_name("Переменное противодавление или необходим сильфон на пружинные ПК по требованию ОЛ", selection_result)
        need_bellows = check_value['response_value'] if check_value and 'response_value' in check_value else None
        check_value = self._get_param_by_name("Материал", selection_result)
        material = check_value['response_value'] if check_value and 'response_value' in check_value else None
        check_value = self._get_param_by_name("Устройство принудительного открытия", selection_result)
        force_open = check_value['response_value'] if check_value and 'response_value' in check_value else None

        is_exist = [valve_type, PN, PN2, DN, T, Ppo, joining_type, need_bellows, material, force_open]
        
        if not all(x is not None for x in is_exist):
            # print(is_exist)
            total_res = list()
            for param in selection_result:
                if "table_name" in param and param["table_name"] in ['table2', 'table3', 'table10', 'table4']:
                    # print(param['name'], 'ЧТО ТАБЛИЧНОЕ?')
                    continue
                # if param['name'] == 'Материал':
                #     param['response_value'] = material
                total_res.append(param)
            return {"total_change": total_res}
            # return {"total_change" : selection_result}
        
        #тип контакта
        err = None
        contact_type_all_values = ["металл-неметалл", "металл-металл"]
        contact_type = None
        if valve_type == "В": #у пружинного - строго металл-металл
            contact_type = "металл-металл"

        elif (valve_type == "П") and (PN > 160):  
            contact_type = "металл-металл"

        elif (valve_type == "П") and (PN <= 160): #если пилотный - по умлочанию металл-неметалл, но можно выбрать
            # contact_type = ["металл-неметалл", "металл-металл"] #можно заменить
            contact_type = None

        else:
            err = f"Некорректое значение типа ПК: {valve_type}"
        #Получаем последний айдишник
        param = self._get_param_by_name("Мембранно-предохранительное устройство", selection_result)
        counter = param['sort'] + 1 #Счетчик для увеличения порядкового номера

        # Выбрал ли что-то пользователь, если это совпадает с расчетным значением, то в response_value записываем выбор пользователя
        user_choice_contact_type = select_formula_params.get("Тип котакта")
        if user_choice_contact_type and contact_type and user_choice_contact_type == contact_type:
            is_response_contact_type = user_choice_contact_type
        #Либо расчетное значение не подходит к выбору пользователя
        elif user_choice_contact_type and not contact_type:
            is_response_contact_type = user_choice_contact_type
        else:
            is_response_contact_type = contact_type
        for param in selection_result:
            if param['name'] == 'Тип котакта':
                param['response_value'] = is_response_contact_type
                break

        # Класс герметичности
        tightness = []
        err_tightness = None
        if valve_type == "П":
            type_contact_for_tightness = contact_type if contact_type else user_choice_contact_type
            if type_contact_for_tightness == "металл-металл":
                tightness = ["С"]
            elif type_contact_for_tightness == "металл-неметалл":
                tightness = ["В", "А", "АА", "С"]
        elif valve_type == "В":
            if DN == 25.0:
                tightness = ["В", "С"]
            else:
                tightness = ["В", "А", "AA", "С"]
        else:
            tightness = None
            err_tightness = f"Невозможно определить класс герметичнности, Некорректое значение типа ПК: {valve_type}"

        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(selection_result, counter_for_id, "Класс герметичности", response_value=tightness, sort=counter_for_sort, error=err_tightness, param_type="raschet")
        # counter += 1

        #подбор фланцев
        if joining_type == "Фланцевое":
            inlet_flange = ['B']#B C D F J K
            if PN == 6.0:
                inlet_flange = ['B', 'C', 'D', 'E', 'F']
            if PN == 16.0:
                inlet_flange = ['B', 'C', 'D', 'E', 'F']
            if PN == 40.0:
                inlet_flange = ['F', 'C', 'D', 'E']
            if PN == 63.0 or PN == 100.0 or PN == 160.0:
                inlet_flange = ['J', 'K', 'F', 'C', 'D', 'E']
            if PN == 250.0:
                inlet_flange = ['K', 'D']
            
            outlet_flange = ['B']#B C D F J K
            
            if PN2 == 6.0:
                outlet_flange = ['B', 'C', 'D', 'E', 'F']
            if PN2 == 16.0 or PN2 == 16.4:
                outlet_flange = ['B', 'C', 'D', 'E', 'F']
            if PN2 == 40.0:
                outlet_flange = ['F', 'C', 'D', 'E']
            if PN2 == 63.0 or PN2 == 100.0 or PN2 == 160.0:
                outlet_flange = ['J', 'K', 'F', 'C', 'D', 'E']
            if PN2 == 250.0:
                outlet_flange = ['K', 'D']

        else:
            inlet_flange = None
            outlet_flange = inlet_flange

        #Фланцы
        user_inlet_flange = select_formula_params.get("Фланец на входе")
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(selection_result, counter_for_id, "Фланец на входе", all_values=inlet_flange, response_value=user_inlet_flange, sort=counter_for_sort, param_type='list')
        # counter += 1

        counter_for_id += 1
        counter_for_sort += 1
        user_outlet_flange = select_formula_params.get("Фланец на выходе")
        res = self._set_params(selection_result, counter_for_id, "Фланец на выходе", all_values=outlet_flange, response_value=user_outlet_flange, sort=counter_for_sort, param_type='list')
        # counter += 1
        
        # Материал сильфона
        counter_for_id += 1
        counter_for_sort += 1
        material_bellows = "08Х18Н10Т" if need_bellows else None
        res = self._set_params(selection_result, counter_for_id, "Материал сильфона", response_value=material_bellows, sort=counter_for_sort, param_type='raschet')
        # counter += 1

        # Испытания
        env_names = list()
        is_mixture = select_formula_params.get("Состав смеси")
        if is_mixture:
            # Если это смесь, то собираем список компонентов
            
            envs_value = select_formula_params.get("Состав смеси")
            for env in envs_value:
                env_value = list(env.keys())[0]
                env_names.append(list(env.keys())[0])
        else:
            env = select_formula_params.get("Название рабочей среды")
            env_names.append(env)

        trials = "По ТУ"
        if "Сероводород" in env_names:
            need = False
            need_M = False

            # s = env_names
            # inx = s.rfind("Сероводород")
            # s_new = s[inx + 12:]
            # r = float(s_new[:s_new.find("%")]) # Какой процент выбрал пользователь
            if not is_mixture:
                r = 100.0
            else:
                for env in is_mixture:
                    if "Сероводород" in env:
                        r = float(env.get("Сероводород"))
            if r > 6.0 and is_mixture:
                need = True

            r *= 0.01
            if Ppo * r >= 0.003:
                need = True

            if need and "Хлор" in env_names:
                need_M = True

            if need:
                # нержавеющее исполнение
                material = "12Х18Н9ТЛ"
                trials = "По СТ ЦКБА 052-2008\n\nИспытания материала корпуса:\n 1) Хим. Состав \n 2) На растяжение при +20 град. С \n 3) KCU при -60 град. С \n 4) Твердость \n 5) Стойкость к МКК \n 6) ВИК \n 7) РК \n 8) Капиллярный контроль \n\nИспытания материала золотника и седла: \n 1) Хим. Состав \n 2) На растяжение при +20 град. С \n 3) Контроль неметаллических включений \n 4) Контроль макроструктуры \n 5) Твердость \n 6) Стойкость к МКК \n 7) ВИК \n 8) РК \n 9) Капиллярный контроль"
            if need_M:
                # молибденовое исполнение
                material = "12Х18Н12М3ТЛ"
                trials = "По СТ ЦКБА 052-2008\n\nИспытания материала корпуса:\n 1) Хим. Состав \n 2) На растяжение при +20 град. С \n 3) KCU при -60 град. С \n 4) Твердость \n 5) Стойкость к МКК \n 6) ВИК \n 7) РК \n 8) Капиллярный контроль \n\nИспытания материала золотника и седла: \n 1) Хим. Состав \n 2) На растяжение при +20 град. С \n 3) Контроль неметаллических включений \n 4) Контроль макроструктуры \n 5) Твердость \n 6) Стойкость к МКК \n 7) ВИК \n 8) РК \n 9) Капиллярный контроль"

        if material == "25Л" and T <= 200:
            material_spool = "20Х13"
        elif material == "25Л" and T > 200:
            material_spool = "12Х18Н10Т"
        elif material == "20ГЛ" and T > 200:
            material_spool = "12Х18Н10Т"
        elif material == "20ГЛ" and T <= 200:
            material_spool = "14Х17Н2"
        elif material == "12Х18Н9ТЛ" and T > 200:
            material_spool = "12Х18Н10Т"
        elif material == "12Х18Н9ТЛ" and T <= 200:
            material_spool = "12Х18Н10Т"
        else:
            material_spool = "10Х17Н13М3Т"

        if material == "25Л":
            color = [
                f"Серый RAL7035 по технологической инструкции 38877941.25206.01013 АО \"НПО Регулятор\" ", #Заводская
                f"Серый RAL7035 cистема АКП С4 по № П2-05 ТИ-0002", #Роснефть
                f"Красный RAL3020 по СТО Газпром 9.1-018-2012", #Газпром
                "Другое"
                ]
        elif material == "20ГЛ":
            color = [
                f"Синий RAL5017 по технологической инструкции 38877941.25206.01013 АО \"НПО Регулятор\" ", #Заводская
                f"Синий RAL5017 система АКП С4 по № П2-05 ТИ-0002", #Роснефть
                f"Красный RAL3020 по СТО Газпром 9.1-018-2012", #Газпром
                "Другое"
                ]
        else:
            color = [
                f"Голубой RAL5012 по технологической инструкции 38877941.25206.01013 АО \"НПО Регулятор\" ", #Заводская
                f"Голубой RAL5012 система АКП С4 по № П2-05 ТИ-0002", #Роснефть
                f"Красный RAL3020 по СТО Газпром 9.1-018-2012", #Газпром
                "Другое"
                ]
        
        #Собираем маркировку
        mark = None
        if valve_type == 'В':
            if force_open == "Да" and need_bellows == "Да":
                mark = "AM211"
                
            elif force_open == "Нет" and need_bellows == "Да":
                mark = "AM212"
            elif force_open == "Да" and need_bellows == "Нет":
                mark = "AM213"
            else:
                mark = "AM214"
        else:
            if force_open == "Да":
                mark = "AM220"
            else:
                mark = "AM219"
        
        # mark = select_formula_params.get("Маркировка")
        if mark:
            weight, painting_area = await self._get_by_mark(db, mark, DN, PN)
            product_drawing = await self._find_param_print(mark, db, 10)
        else:
            weight = None # "Маccа"
            painting_area = None # "Площадь под покраску"
            product_drawing = None 
        print(product_drawing, 'Получили изображение')
        packaging = [
            "Упаковка на европаллет (1200х800)",
            "Упаковка груза в ящики из OSB по ТУ “АО НПО Регулятор”",
            "Упаковка груза в ящики из OSB по ТУ “АО НПО Регулятор”  в северном исполнении",
            "Упаковка груза в ящики из OSB по ТУ “АО НПО Регулятор”  в морском исполнении",
            "Упаковка груза в дощатые ящики по ГОСТ 10198",
            "Упаковка груза в дощатые ящики по ГОСТ 10198 в северном исполнении",
            "Упаковка груза в дощатые ящики по ГОСТ 10198 в морском исполнении"
            ]
        
        if DN <= 50:
            packaging.insert(1, "Пенная защитная упаковка груза")

        assignment = "25 лет" if need_bellows else "30 лет"

        
        # material_spool "Материал золотника"
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(selection_result, counter_for_id, "Материал золотника", response_value=material_spool, sort=counter_for_sort, param_type='raschet')
        # counter += 1

        # weight Маccа
        counter_for_id += 1
        counter_for_sort += 1 
        res = self._set_params(selection_result, counter_for_id, "Маccа", response_value=float(weight), sort=counter_for_sort, param_type='raschet')
        # counter += 1

        # painting_area Площадь под покраску
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(selection_result, counter_for_id, "Площадь под покраску", response_value=float(painting_area), sort=counter_for_sort, param_type='raschet')
        # counter += 1

        # assignment Срок службы
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(selection_result, counter_for_id, "Срок службы", response_value=assignment, sort=counter_for_sort, param_type='raschet')
        # counter += 1

        # color Цвет
        counter_for_id += 1
        counter_for_sort += 1
        user_color = select_formula_params.get("Цвет")
        res = self._set_params(selection_result, counter_for_id, "Цвет", all_values=color, response_value=user_color, sort=counter_for_sort, param_type='list')
        # counter += 1

        # packaging Упаковка
        counter_for_id += 1
        counter_for_sort += 1
        user_packaging = select_formula_params.get("Упаковка")
        res = self._set_params(selection_result, counter_for_id, "Упаковка", all_values=packaging, response_value=user_packaging, sort=counter_for_sort, param_type='list')
        # counter += 1

        # trials Испытания
        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(selection_result, counter_for_id, "Испытания", response_value=trials, sort=counter_for_sort, param_type='raschet')
        # counter += 1

        #Собираем маркировку
        MARK_ARR[0] = mark
        MARK_ARR[1] = str(int(DN))
        MARK_ARR[2] = str(int(PN))
        connection_params = {
            "В": {
                "Фланцевое": "3",
                "Под приварку": "4",
                "Цапковое": "1",
                "Штуцерно-торцовое": "2",
                "Штуцерное": "5",
                "Муфтовое": "6",
                "Ниппельное": "7",
                "Кламповое": "8"
            },
            "П": {
                "Фланцевое": "3",
                "Под приварку": "4",
                "Цапковое": "7",
                "Штуцерно-торцовое": "9",
                "Штуцерное": "6",
                "Муфтовое": "8",
                "Ниппельное": "5",
                "Кламповое": "2"
            }
        }
        MARK_ARR[3] = connection_params[valve_type].get(joining_type, "X")
        contact_params = {
            "металл-неметалл": "2",
            "металл-металл": "3",
        }
        if not contact_type:
            MARK_ARR[4] = contact_params.get(user_choice_contact_type, "X")
        else:
            MARK_ARR[4] = contact_params.get(contact_type, "X")

        material_params = {
            "25Л": "1",
            "12Х18Н9ТЛ": "2",
            "20ГЛ": "3",
            "12Х18Н12М3ТЛ": "4"
        }
        MARK_ARR[5] = material_params.get(material, "X")
        open_close_type_dict = {
            "открытого типа": "1",
            "закрытого типа": "0"
        }
        open_close_type = self._get_param_by_name("Открытый / Закрытый тип", res)
        if open_close_type:
            MARK_ARR[6] = open_close_type_dict.get(open_close_type['response_value'], "X")
        else:
            MARK_ARR[6] = "X"
        if user_inlet_flange and user_outlet_flange and joining_type == "Фланцевое": 
            MARK_ARR[7] = f'{user_inlet_flange}/{user_outlet_flange}'
        else:
            MARK_ARR[7] = ""
        total_mark = ''
        total_mark += '.'.join(MARK_ARR)

        counter_for_id += 1
        counter_for_sort += 1
        res = self._set_params(res, counter_for_id, "Маркировка", response_value=total_mark, sort=counter_for_sort, param_type='raschet')
        # counter += 1

        #изменился Материал material
        total_res = list()
        for param in res:
            if "table_name" in param and param["table_name"] in ['table2', 'table3', 'table10', 'table4']:
                # print(param['name'], 'ЧТО ТАБЛИЧНОЕ?')
                continue
            if param['name'] == 'Материал':
                param['response_value'] = material

            # if 'response_value' not in param:
            #     print(param['name'], 123123)

            total_res.append(param)
        # Параметры без response_value
        # Молекулярная масса 123123

        # Удельная изобарная теплоемкость кДж/(кг*К) 123123

        # Тип котакта 123123

        # Класс герметичности 123123
        return {"total_change": total_res}
    
    async def safety_valve_drawing(self, selection_result, param_info, select_formula_params, db, column_to_param=[]):
        pass

    async def agent_contacts(self, selection_result, param_info, select_formula_params, db, column_to_param=[]):
        """
        Параметры для заполнения контактов агента:
        - Имя агента (agent_name)
        - Телефон агента (agent_phone)
        - Email агента (agent_email)
        - Организация агента (agent_organization)
        """
        param = self._get_param_by_name("Цена /шт. руб с НДС 22%", selection_result)
        counter = param['sort'] + 1
        res = []
        contact_info = ["ФИО Заказчика", "Телефон Заказчика", "Email Заказчика", "Организация Заказчика"]
        
        result = self._set_params(selection_result, counter, "ФИО Заказчика", sort=counter, param_type='user_input')
        counter += 1
        result = self._set_params(result, counter, "Телефон Заказчика",sort=counter, param_type='user_input')
        counter += 1
        result = self._set_params(result, counter, "Email Заказчика", sort=counter, param_type='user_input')
        counter += 1
        result = self._set_params(result, counter, "Организация Заказчика", sort=counter, param_type='user_input')
        counter += 1
        result = self._set_params(result, counter, "Проектная организация", sort=counter, param_type='user_input')
        counter += 1
        result = self._set_params(result, counter, "Комментарий", sort=counter, param_type='user_input')
        counter += 1
        result = self._set_params(result, counter, "Должность Заказчика", sort=counter, param_type='user_input')
        counter += 1
        result = self._set_params(result, counter, "Адрес Заказчика", sort=counter, param_type='user_input')

        if not select_formula_params:
            return {"total_change" : result}
        for param in result:
            if param['name'] in contact_info and param['name'] in select_formula_params:
                param['responce_value'] = select_formula_params[param['name']]
            res.append(param)
        return {"total_change" : res}
        
            
        


ALLOWED_FUNCTIONS =  [method for method in dir(CodeParametr) if callable(getattr(CodeParametr, method)) and not method.startswith("__")]