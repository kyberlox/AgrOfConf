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

        # поиск смеси среди выбранных значений
        if select_formula_params != []:
            for param_name, value in select_formula_params.items():
                if param_name == "Смесь":
                    naydeno = True
                    if value == "Да":
                        res = self._set_params(res, param_info.id, param_info.name, param_description=param_info.description, all_values=["Да", "Нет"], response_value="Да", sort=1)
                        is_mixture = True

                    elif value == "Нет":
                        res = self._set_params(selection_result, param_info.id, param_info.name, param_description=param_info.description, all_values=["Да", "Нет"], response_value="Нет", sort=1)
                        
        if not naydeno:
            res = self._set_params(res, 1, "Смесь", all_values=["Да", "Нет"], sort=1)
        
        if is_mixture:
            #список ВСЕХ сред
            param = self._get_param_by_name("Название рабочей среды", selection_result)
            all_values = param["all_values"]
            envs_param = [value for param_name, value in select_formula_params.items() if param_name == "Состав смеси"]
            
            if not envs_param:
                description = "Нужно выбрать состав смеси из списка доступных сред и указать их мольные доли (%)"
                res = self._set_params(res, param_info.id, "Состав смеси", param_description=description, all_values=all_values, sort=2, param_type="select-input")

            elif envs_param:
                #проверить правильность
                envs = envs_param[0]
                #сумма мольных долей
                r_sum = sum(list(env.values())[0] for env in envs)
                
                #хватает ли сред для смеси
                if envs == [] or len(envs) == 1:
                    description = "Нужно выбрать состав смеси из списка доступных сред и указать их мольные доли (%)"
                    error = "Смесь не может состоять менее чем из двух сред!"
                    res = self._set_params(res, param_info.id, "Состав смеси", param_description=description, all_values=all_values, sort=2, param_type="select-input", response_value=envs, error=error)

                #праивльная ли сумма их долей?
                elif r_sum != 100:
                    description = "Нужно выбрать состав смеси из списка доступных сред и указать их мольные доли (%)"
                    error = f"Сумма мольных долей сред смеси должна составлять 100%, а не {r_sum}%"
                    res = self._set_params(res, param_info.id, "Состав смеси", param_description=description, all_values=all_values, sort=2, param_type="select-input", response_value=envs, error=error)
                
                #если всё правильно
                else:
                    description = "Нужно выбрать состав смеси из списка доступных сред и указать их мольные доли (%)"
                    # res = self._set_params(res, param_info.id, "Состав смеси", param_description=description, all_values=all_values, sort=2, param_type="select-input", response_value=envs)
                    got_envs = True

        #климатика
        if got_envs:
            #список ВСЕХ климатик
            climate = self._get_param_by_name("Климатическое исполнение по ГОСТ 15150-69", selection_result)['all_values']
            type_param = [value for param_name, value in select_formula_params.items() if param_name == "Климатическое исполнение по ГОСТ 15150-69"]
            
            climate_values = type_param[0] if type_param else None # is not None
            #если нет
            if climate_values is None:
                res = self._set_params(res, param_info.id, "Климатическое исполнение по ГОСТ 15150-69", all_values=climate, sort=3)
            else:
                res = self._set_params(res, param_info.id, "Климатическое исполнение по ГОСТ 15150-69", all_values=climate, sort=3, response_value=climate_values)
                got_climate = True

        #Тип клапана
        if got_climate:
            #список ВСЕХ климатик
            all_type_names = self._get_param_by_name("Тип клапана", selection_result)["all_values"]
            # type_param = self._get_param_by_name("Тип предохранительного клапана", select_formula_params)
            type_param = [value for param_name, value in select_formula_params.items() if param_name == "Тип клапана"]
            
            type_val = type_param[0] if type_param else None # is not None

            #если нет
            if type_val is None:
                res = self._set_params(res, param_info.id, "Тип клапана", all_values=all_type_names, sort=4)

            #валидация нужна
            elif type_val not in all_type_names:
                error = "Надо выбрать один из предложеннных вариантов"
                res = self._set_params(res, param_info.id, "Тип клапана", all_values=all_type_names, sort=4, error=error, response_value=type_val)

            else:
                res = self._set_params(res, param_info.id, "Тип клапана", all_values=all_type_names, sort=4, response_value=type_val)
                got_type = True
        
        #Температура
        if got_type:
            # задана пользователем?
            # T_param  = self._get_param_by_name("Температура рабочей среды", select_formula_params)
            T_param  = [value for param_name, value in select_formula_params.items() if param_name == "Температура рабочей среды"]
            T = int(T_param[0]) if T_param else None

            description = "Ввведите значение температуры рабочей среды (°C)"
            required_type = "user_input"
            response_value = T
            
            #если нет
            if T is None:
                res = self._set_params(res, param_info.id, "Температура рабочей среды", param_description=description, all_values=all_type_names, sort=5, param_type=required_type)
            
            #валидировать:
            elif (type_val == "Пружинный (В)" and (T < -60 or T > 600) ) or (type_val == "Пилотный (П)" and (T < -60 or T > 250) ):
                error = "Температура должна быть в диапазоне от -60°С до 600°С для пружинных и от -60°С до 250°С для пилотных клапанов"
                res = self._set_params(res, param_info.id, "Температура рабочей среды", param_description=description, all_values=all_type_names, sort=5, param_type=required_type, response_value=response_value, error=error)
            
            else:
                res = self._set_params(res, param_info.id, "Температура рабочей среды", param_description=description, all_values=all_type_names, sort=5, param_type=required_type, response_value=response_value)

                got_T = True

        ################# РАСЧЕТ #################
        if got_T:
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
                print(env_result, "ЧЕ получили перед ошибкой")
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
                env_type_name = f"Однородная смесь - {list(env_type)[0]}"
                result["agregatnoe_sostojanie"] = env_type_name

                if list(env_type)[0] == "Жидкость":
                    ch_den = 0
                    zn_den = 0
                    pre_viscosity = 0
                    for env in envs_json:
                        r = env["r"]
                        result["nazvanie_rabochej_sredy"] += f"{env['name']}:{r}% "
                        result["molekuljarnaja_massa"] += float(env["molecular_weight"]) * r
                        ch_den += float(env["density"]) * r
                        zn_den += r
                        pre_viscosity += log10(float(env["viscosity"])) * r


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

                    r = env["r"]
                    result["nazvanie_rabochej_sredy"] += f"{env['name']}:{r}% "

                    # pre_viscosity += log10(env["viscosity"]) * r

                    if env["environment"] == "Газ":
                        M = float(env["molar_mass"])
                        density_ch += (float(env["molar_mass"]) / 22.4) * r
                        density_zn += r
                    elif env["environment"] == "Жидкость":
                        M = float(env["molecular_weight"])
                        density_ch += float(env["density"]) * r
                        density_zn += r

                    pre_u += r * float(env["viscosity"]) * M

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
            if ((climate == "ХЛ1") or (climate == "УХЛ1")) and (result["material"] == "25Л"):
                if T < 350.0:
                    result["material"] = "20ГЛ"
                elif T >= 350.0 and climate == "ХЛ1":
                    result["material"] = "12Х18Н9ТЛ"


            for param_name, value in result.items():
                kir_param_name = column_to_param[param_name]
                param_info = [param for param in selection_result if param["name"] == kir_param_name]
                if not param_info:
                    continue
                param_info = param_info[0]
                res = self._set_params(res, param_info['id'], kir_param_name, param_description=param["description"], all_values=param_info['all_values'], response_value=value, sort=param_info['sort'])
            
            #Поскольку расчет смеси завершился, докидываем
            # параметры из БД для следующего расчета
            for param_db in selection_result:
                param_info = [param_res for param_res in res if 'debug' not in param_res and param_res["name"] == param_db["name"]]
                if param_info:
                    continue
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
        print(DNS, PN, valve_type)
        #найти все подходящие строки их DNS и P1 - больше искомых
        # request = db.query(Params).filter(Params.DNS >= DNS, Params.PN == PN, Params.valve_type == valve_type).all()
        query = """
            SELECT * FROM table3 
            WHERE dns3::float >= :DNS_val 
            AND pn3::float >= :Pn_val
            AND tip_predohranitel_nogo_klapana = :valve_type
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

            try:
                Pn1 = str(example.pnd3).split("...")[0]
                Pn2 = str(example.pnd3).split("...")[1]
                #print(Pn1, Pn2)

                #print(f"example.DNS <= minDNS {example.DNS <= minDNS} example.PN == minPN {example.PN == minPN} float(Pn1) <= Pn <= float(Pn2) {float(Pn1)} {Pn} {float(Pn2)} {float(Pn1) <= Pn <= float(Pn2)}")
                if (example.dns3 <= minDNS)  and (example.pn3 == minPN) and (float(Pn1) <= Pn <= float(Pn2)):
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
                elif (Pn <= float(Pn2)) and (Pn <= 4) and (example.dns3 <= minDNS)  and (example.pn3 == minPN):
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
        last_sort = 0
        selection_result.pop(0)
        res = deepcopy(selection_result)
        #Ищем Устройство принудительного открытия
        for param_name, value in select_formula_params.items():
            if param_name == "Устройство принудительного открытия":
                force_open = value
                #ищем данные параметра
                param_info = [param for param in selection_result if param["name"] == param_name]
                if not param_info:
                    return {'error': 'Не найден параметр в БД - Устройство принудительного открытия'}
                param_info = param_info[0]
                # res = self._set_params(res, param_info['id'], param_name, param_description=param_info['description'], all_values=["Да", "Нет"], response_value=value, sort=param_info['sort'])
                last_sort = param_info['sort']
            elif param_name == "Давление настройки" and force_open:
                Pn = value
                last_sort += 1
                if value > 16 or value < 0:
                    res = self._set_params(res, last_sort, param_name, param_description="", all_values=[0, 16], response_value=value, sort=last_sort, error="Давление настройки не может быть меньше 0 и больше 16")
                    continue
                res = self._set_params(res, last_sort, param_name, param_description="", all_values=[0, 16], response_value=value, sort=last_sort)
            elif param_name == "Максимальный аварийный расход жидкости и газа" and force_open:
                Gab = value
                last_sort += 1
                if value < 0:
                    res = self._set_params(res, last_sort, param_name, param_description="", all_values=[0, 10 ** 100], response_value=value, sort=last_sort, error="Значение не может быть меньше 0")
                    continue
                res = self._set_params(res, last_sort, param_name, param_description="", all_values=[0, 10 ** 100], response_value=value, sort=last_sort)
            elif param_name == "Количество параллельно установленных и одновременно работающих клапанов (шт)" and force_open:
                N = value
                last_sort += 1
                if value < 0:
                    res = self._set_params(res, last_sort, param_name, param_description="", all_values=[0, 10 ** 100], response_value=value, sort=last_sort)
                continue
                res = self._set_params(res, last_sort, param_name, param_description="", all_values=[0, 10 ** 100], response_value=value, sort=last_sort, error="Значение не может быть меньше 0")
            elif param_name == "Мембранно-предохранительное устройство" and force_open:
                pre_Kc = value
                last_sort += 1
                res = self._set_params(res, last_sort, param_name, param_description="", all_values=["Да", "Нет"], response_value=value, sort=last_sort)
            elif param_name == "Противодавление статическое" and Pn:
                last_sort += 1
                Pp = value
                if value > Pn * 0.7 or value < 0:
                    res = self._set_params(res, last_sort, "Противодавление статическое", param_description="", all_values=[0, Pn * 0.7], response_value=value, sort=last_sort, error="Значение не может быть больше 70% давления настройки и меньше 0")
                else:
                    
                    last_sort += 1
                    res = self._set_params(res, last_sort, "Противодавление статическое", param_description="", all_values=[0, Pn * 0.7], response_value=value, sort=last_sort)
            elif param_name == "Противодавление динамическое" and Pn:
                last_sort += 1
                Pp_din = value
                if value > Pn * 0.7 or value < 0:
                    res = self._set_params(res, last_sort, "Противодавление динамическое", param_description="", all_values=[0, Pn * 0.7], response_value=value, sort=last_sort, error="Значение не может быть больше 70% давления настройки и меньше 0")
                else:
                    res = self._set_params(res, last_sort, "Противодавление динамическое", param_description="", all_values=[0, Pn * 0.7], response_value=value, sort=last_sort)

        #Формируем Устройство принудительного открытия
        if not force_open:
            {"total_change" : res}
        #Формируем Давление настройки
        if not Pn and force_open:
            last_sort += 1
            res = self._set_params(res, last_sort, "Давление настройки", param_description="", all_values=[0, 16], sort=last_sort)
        #Формируем Максимальный аварийный расход жидкости и газа
        if not Gab and force_open:
            last_sort += 1
            res = self._set_params(res, last_sort, "Максимальный аварийный расход жидкости и газа", param_description="", all_values=[0, 10 ** 100], sort=last_sort)
        #Формируем Количество параллельно установленных и одновременно работающих клапанов (шт)
        if not N and force_open:
            last_sort += 1
            res = self._set_params(res, last_sort, "Количество параллельно установленных и одновременно работающих клапанов (шт)", param_description="", all_values=[0, 10 ** 100], sort=last_sort)
        #Формируем Мембранно-предохранительное устройство
        if not pre_Kc and force_open:
            last_sort += 1
            res = self._set_params(res, last_sort, "Мембранно-предохранительное устройство", param_description="", all_values=["Да", "Нет"], sort=last_sort)
        #Формируем Противодавление статическое
        if not Pp and Pn:
            last_sort += 1
            res = self._set_params(res, last_sort, "Противодавление статическое", param_description="", all_values=[0, Pn * 0.7], sort=last_sort)
        #Формируем Противодавление динамическое
        if not Pp_din and Pn:
            last_sort += 1
            res = self._set_params(res, last_sort, "Противодавление динамическое", param_description="", all_values=[0, Pn * 0.7], sort=last_sort)
        
        #Если не все заполнено, возвращаем массив параметров для заполнения
        is_exist = [force_open, Pn, Gab, N, pre_Kc, Pp, Pp_din]
        if not all(x is not None for x in is_exist):
            return {"total_change" : res}
        
        #Все заполнено, можно выполнять расчет
        P_atm = 0.101320
        R = 8.31446261815324  # Газовая постоянная ( Па / (моль * K))
        u_info = [param for param in res if param["name"] == 'Вязкость (Па*с)']
        u = u_info[0]["response_value"]

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
            density_inf = [param for param in selection_result if param["name"] == 'Плотность жидкости']
            p1 = density_inf["response_value"]
        
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
                    Kb = B ** 2 * -2 * exp * log(B)  # на самом деле, тут корень, но его будем извлекать в конце
                else:
                    Kb = (((n + 1) / (n - 1)) * (B ** (2 / n) - B ** ((n + 1) / n)) * ((n + 1) / 2)) ** 2

            # P1 * p1
            Gideal = Kp_kr * Kb * sqrt(P1 * p1)

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
            Gideal = Kp * sqrt(P1 * p1)

            if Gideal <= 0:
                return {'error': 'ошибка расчетов, Gideal <= 0 там где среда не газ'}
        
        DN_s = None
        pre_DN = 0
        Kv = 1

        while DN_s != pre_DN:

            pre_F = Gab / (3.6 * alpha * Kv * Kw * Kc * Gideal * N)
            print(pre_F, ":", Gab, alpha, Kv, Kw, Kc, Gideal, N)
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
            return {"error": "Нет возможности подобрать PN"}

        param = self._get_param_by_name("Тип клапана", selection_result)
        valve_type = param["response_value"][-2]
        example = await self._searchParams(db, float(DN_s), Pn * 10.197162, int(PN), valve_type)

        #Собираем ответ
        #Получаем последний айдишник
        param = self._get_param_by_name("Мембранно-предохранительное устройство", res)
        counter = param['sort'] + 1 #Счетчик для увеличения порядкового номера

        #Минимальная рабочая температура
        res = self._set_params(res, counter, "Минимальная рабочая температура", param_type='raschet', response_value=T_min, sort=counter, visibility=False)
        counter += 1
        #Максимальная рабочая температура
        res = self._set_params(res, counter, "Максимальная рабочая температура", param_type='raschet', response_value=T_max, sort=counter, visibility=False)
        counter += 1
        # Давление начала открытия с противодавлением
        res = self._set_params(res, counter, "Давление начала открытия с противодавлением", param_type='raschet', response_value=Pno * 10.197162, sort=counter)
        counter += 1
        # Давление полного открытия с противодавлением
        res = self._set_params(res, counter, "Давление полного открытия с противодавлением", param_type='raschet', response_value=Ppo * 10.197162, sort=counter)
        counter += 1
        # Давление на входе
        res = self._set_params(res, counter, "Давление на входе", param_type='raschet', response_value=P1 * 10.197162, sort=counter)
        counter += 1
        # Давление на выходе
        res = self._set_params(res, counter, "Давление на выходе", param_type='raschet', response_value=P2 * 10.197162, sort=counter)
        counter += 1
        # Коэффициент, учитывающий эффект неполного открытия разгруженных ПК из-за противодавления
        res = self._set_params(res, counter, "Коэффициент, учитывающий эффект неполного открытия разгруженных ПК из-за противодавления", param_type='raschet', response_value=Kw, sort=counter)
        counter += 1
        # Массовая скорость
        res = self._set_params(res, counter, "Массовая скорость", param_type='raschet', response_value=Gideal, sort=counter)
        counter += 1
        # Предварительный Диаметр седла клапана, мм
        res = self._set_params(res, counter, "Диаметр седла клапана, мм:", param_type='raschet', response_value=DN_s, sort=counter)
        counter += 1
        # Номиннальный диаметр седла !f example:
        res = self._set_params(res, counter, "Номиннальный диаметр седла", param_type='raschet', response_value=example["DNS"], sort=counter)
        counter += 1
        # Номиннальный диаметр !f example:
        res = self._set_params(res, counter, "Номиннальный диаметр", param_type='raschet', response_value=example["DN"], sort=counter)
        counter += 1
        # Номиннальное давление !f example:
        res = self._set_params(res, counter, "Номиннальное давление", param_type='raschet', response_value=example["PN"], sort=counter)
        counter += 1
        # Номиннальный диаметр на выходе
        DN2 = {
            25.0: 40.0,
            50.0: 80.0,
            80.0: 100.0,
            100.0: 150.0,
            150.0: 200.0,
            200.0: 300.0
        }
        res = self._set_params(res, counter, "Номиннальный диаметр на выходе", param_type='raschet', response_value=DN2[int(example["DN"])], sort=counter)
        counter += 1
        # Номинальное давление на выходе
        PN2 = {
            16.0: 6,
            40.0: 16.0,
            63.0: 40.0,
            100.0: 40.0,
            160.0: 40.0,
            250.0: 40.0
        }
        res = self._set_params(res, counter, "Номинальное давление на выходе", param_type='raschet', response_value=PN2[int(example["PN"])], sort=counter)
        counter += 1
        # Площадь седла клапана
        DN_s = int(example["DNS"])
        S = (pi * DN_s**2 )/ 4
        res = self._set_params(res, counter, "Площадь седла клапана", param_type='raschet', response_value=S, sort=counter)
        counter += 1
        # Эффективная площадь седла калапана
        res = self._set_params(res, counter, "Эффективная площадь седла калапана", param_type='raschet', response_value=S * alpha, sort=counter)
        counter += 1
        # Материал пружины
        res = self._set_params(res, counter, "Материал пружины", param_type='raschet', response_value=example["spring_material"], sort=counter, visibility=False)
        counter += 1
        # Номер пружины
        res = self._set_params(res, counter, "Номер пружины", param_type='raschet', response_value=example["spring_number"], sort=counter, visibility=False)
        counter += 1
        # Диапазон давлений настройки
        res = self._set_params(res, counter, "Диапазон давлений настройки", param_type='raschet', response_value=example["Pnd"], sort=counter, visibility=False)
        counter += 1
        # Переменное противодавление или необходим сильфон на пружинные ПК по требованию ОЛ
        new_list = []
        for param in res:
            if 'table_name' in param:
                continue
            new_list.append(param)

        return {"total_change" : new_list}

    async def mark_params(self, selection_result, param_info, select_formula_params, db, column_to_param=[]):
        """
        Параметры которые нужны для расчета:
        - Тип предохранительного клапана Пружинный или Пилотный (B/H) (valve_type)
        - Номинальное давление (PN)
        - Номинальное давление на выходе (PN2)
        - Номиннальный диаметр (DN)
        - Температура рабочей среды (T)
        - Тип присоединения (joining_type)
        - Переменное противодавление или необходим сильфон на пружинные ПК по требованию ОЛ (need_bellows)
        - Маркировка (mark)
        """
        # need_bellows = False
        # if (dt["valve_type"] == 'В') and (((example["spring_material"] == '51ХФА') and (T > 120)) or ((example["spring_material"] == '50ХФА') and (T > 250))):
        #     new_dt["need_bellows"] = True
        # # elif dt["valve_type"] == 'В':
        # #         new_dt["need_bellows"] = [True, False]

        # # вода агрессиваня?
        # cool_env = ["Вода", "Водяной пар", "Воздух", "Азот", "Вода"]


        # cool = 0
        # for en in env_names:
        #     # убрать из смеси неагрессивные среды
        #     if en in cool_env:
        #         # print(en)
        #         cool += 1
        # open_close_type = "закрытого типа"
        # if cool == len(env_names) and (dt["valve_type"] == 'В') and (((example["spring_material"] == '51ХФА') and (T > 120)) or ((example["spring_material"] == '50ХФА') and (T > 250))):

        #     if T:
        #         open_close_type = "открытого типа"
        #         dt["need_bellows"] = False
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
        contact_info = ["ФИО заказчика", "Телефон заказчика", "Email заказчика", "Организация заказчика"]
        
        result = self._set_params(selection_result, counter, "ФИО заказчика", sort=counter, param_type='user_input')
        counter += 1
        result = self._set_params(result, counter, "Телефон заказчика",sort=counter, param_type='user_input')
        counter += 1
        result = self._set_params(result, counter, "Email заказчика", sort=counter, param_type='user_input')
        counter += 1
        result = self._set_params(result, counter, "Организация заказчика", sort=counter, param_type='user_input')
        counter += 1
        result = self._set_params(result, counter, "Проектная организация", sort=counter, param_type='user_input')
        counter += 1
        result = self._set_params(result, counter, "Комментарий", sort=counter, param_type='user_input')
        counter += 1
        result = self._set_params(result, counter, "Должность заказчика", sort=counter, param_type='user_input')
        counter += 1
        result = self._set_params(result, counter, "Адрес заказчика", sort=counter, param_type='user_input')

        if not select_formula_params:
            return {"total_change" : result}
        for param in result:
            if param['name'] in contact_info and param['name'] in select_formula_params:
                param['responce_value'] = select_formula_params[param['name']]
            res.append(param)
        return {"total_change" : res}
        
            
        


ALLOWED_FUNCTIONS =  [method for method in dir(CodeParametr) if callable(getattr(CodeParametr, method)) and not method.startswith("__")]