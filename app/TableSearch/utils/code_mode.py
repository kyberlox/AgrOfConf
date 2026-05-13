from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

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
                "visibility" : visibility
            }
        if param_type == "list":
            new_param["all_values"] = all_values

        if response_value:
            new_param["response_value"] = response_value
        if error:
            new_param["error"] = error
        if sort:
            new_param["sort"] = sort

        selection_result.append(new_param)

        return selection_result
    
    async def make_mixture(self, selection_result, param_info, select_formula_params, db):
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
                        res = self._set_params(res, param_info.id, param_info.name, param_description=param_info.description, all_values=["Да", "Нет"], response_value="Да")
                        is_mixture = True

                    elif value == "Нет":
                        res.append(mixture)
                        res = self._set_params(res, param_info.id, param_info.name, param_description=param_info.description, all_values=["Да", "Нет"], response_value="Нет")

        if not naydeno:
            res = self._set_params(res, 0, "Смесь", all_values=["Да", "Нет"])
        
        if is_mixture:
            #список ВСЕХ сред
            param = self._get_param_by_name("Название рабочей среды", selection_result)
            all_values = param["all_values"]
            res = self._set_params(res, param["id"], param["name"], param_description=param["description"], all_values=all_values)

        
        return {"total_change" : res}


    async def old_make_mixture(self, selection_result, param_info, select_formula_params, db):
        """
        алгоритм подбора смеси
        """
        # print(selection_result)
        # print(param_info)
        # print(select_formula_params)
        res = []
        #чтобы не падала ошибка табличного подбора
        debug_param = {
            "id" : -1,
            "debug" : False,
            'visibility': False
        }

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
                        mixture = {
                            'id': 0,
                            'name': param_info.name,
                            'description': param_info.description,
                            'visibility': False,
                            'response_value': 'Да'
                        }

                        res.append(mixture)
                        is_mixture = True

                    elif value == "Нет":
                        
                        mixture = {
                            'id': param_info.id,
                            'name': param_info.name,
                            'description': param_info.description,
                            'visibility': False,
                            'response_value': 'Нет'
                        }
                        res.append(mixture)

                        # return {"total_change" : res}

        # внедрить параметр для смеси на какое-нибудь место, если её ещё нет
        if not naydeno:
            res = [
                debug_param,
                {
                    'id': 0,
                    'name': param_info.name,
                    'description': param_info.description,
                    'visibility': True,
                    'required_type':  "list",
                    "all_values": [
                        "Да",
                        "Нет"
                    ]
                }
            ]
        
        #заполняем смесь
        if is_mixture:
            #список ВСЕХ сред
            all_envs_names = self._get_param_by_name("Название рабочей среды", selection_result)["all_values"]

            #есть ли параметр для состава смесей?
            # envs_param = self._get_param_by_name("Состав смеси", selection_result)
            envs_param = [value for param_name, value in select_formula_params.items() if param_name == "Состав смеси"]
            
            #если нет
            if not envs_param:

                #создать
                envs_values = {
                    'id': 1,
                    'name': "Состав смеси",
                    'description': "Нужно выбрать состав смеси из списка доступных сред и указать их мольные доли (%)",
                    # "code_example" : [{ "Азот" : 50}, {"Воздух" : 50}],
                    'visibility': True,
                    'required_type':  "select-input",
                    "all_values": all_envs_names
                }

                # res = [debug_param, mixture, envs_values]
                res.append(envs_values)
                # return {"total_change" : res}
            
            #если есть
            elif envs_param:
                #проверить правильность
                envs = envs_param[0]
                #сумма мольных долей
                r_sum = sum(list(env.values())[0] for env in envs)
                
                #хватает ли сред для смеси
                if envs == [] or len(envs) == 1:
                    envs_values = {
                        'id': 1,
                        'name': "Состав смеси",
                        'description': "Нужно выбрать состав смеси из списка доступных сред и указать их мольные доли (%)",
                        # "code_example" : [{ "Азот" : 50}, {"Воздух" : 50}],
                        'visibility': True,
                        'required_type':  "select-input",
                        "all_values": all_envs_names,
                        "response_value" : envs,
                        "error" : "Смесь не может состоять менее чем из двух сред!"
                    }

                    # res = [debug_param, mixture, envs_values]
                    res.append(envs_values)

                #праивльная ли сумма их долей?
                elif r_sum != 100:
                    envs_values = {
                        'id': 1,
                        'name': "Состав смеси",
                        'description': "Нужно выбрать состав смеси из списка доступных сред и указать их мольные доли (%)",
                        # "code_example" : [{ "Азот" : 50}, {"Воздух" : 50}],
                        'visibility': True,
                        'required_type':  "select-input",
                        "all_values": all_envs_names,
                        "response_value" : envs,
                        "error" : f"Сумма мольных долей сред смеси должна составлять 100%, а не {r_sum}%"
                    }

                    # res = [debug_param, mixture, envs_values]
                    res.append(envs_values)

                #если всё правильно
                else:
                    envs_values = {
                        'id': 1,
                        'name': "Состав смеси",
                        'description': "Нужно выбрать состав смеси из списка доступных сред и указать их мольные доли (%)",
                        # "code_example" : [{ "Азот" : 50}, {"Воздух" : 50}],
                        'visibility': True,
                        'required_type':  "select-input",
                        "all_values": all_envs_names,
                        "response_value" : envs
                    }

                    # res = [debug_param, mixture, envs_values]
                    res.append(envs_values)
                    # print("envs собран!")
                    got_envs = True
        
        #климатика
        if got_envs:
            # '''
            #список ВСЕХ климатик
            climate = self._get_param_by_name("Климатическое исполнение по ГОСТ 15150-69", selection_result)
            climate_values = climate
            if "response_value" not in climate:
                climate["id"] = 2
                # res = [debug_param, mixture, envs_values, climate_values]
                res.append(climate_values)
                return {"total_change" : res}

            # selection_result = [debug_param, mixture, envs_values, climate_values]
            res.append(climate_values)
            got_climate = True
            '''
            all_climate_names = self._get_param_by_name("Климатическое исполнение по ГОСТ 15150-69", selection_result)["all_values"]
            # print("climate", all_climate_names)
            

            climate_param = self._get_param_by_name("Климатическое исполнение (ГОСТ 15150-69)", select_formula_params)
            # print("climate_param", climate_param)

            climate = climate_param["response_value"] if climate_param is not None else None
            # print("climate", climate)
            

            #если нет
            if climate is None:
                #создать
                climate_values = {
                    'id': 2,
                    'name': "Климатическое исполнение (ГОСТ 15150-69)",
                    'description': "",
                    'visibility': True,
                    'required_type':  "list",
                    "all_values": all_climate_names
                }

                selection_result = [debug_param, mixture, envs_values, climate_values]

            #валидация нужна
            elif climate not in all_climate_names:
            
                
                climate_values = {
                    'id': 2,
                    'name': "Климатическое исполнение (ГОСТ 15150-69)",
                    'description': "",
                    'visibility': True,
                    'required_type':  "list",
                    "all_values": all_climate_names,
                    "response_value" : climate,
                    "error" : "Надо выбрать один из предложеннных вариантов"
                }

                selection_result = [debug_param, mixture, envs_values, climate_values]
            
            else:
                #собрал климатику
                climate_values = {
                    'id': 2,
                    'name': "Климатическое исполнение (ГОСТ 15150-69)",
                    'description': "",
                    'visibility': True,
                    'required_type':  "list",
                    "all_values": all_climate_names,
                    "response_value" : climate
                }
            got_climate = True
            '''
                # got_climate = True

        #Тип клапана
        if got_climate:
            #список ВСЕХ климатик
            all_type_names = self._get_param_by_name("Тип клапана", selection_result)["all_values"]
            # type_param = self._get_param_by_name("Тип предохранительного клапана", select_formula_params)
            type_param = [value for param_name, value in select_formula_params.items() if param_name == "Тип предохранительного клапана"]
            
            type_val = type_param[0] if type_param else None # is not None

            #если нет
            if type_val is None:
                #создать
                type_values = {
                    'id': 3,
                    'name':"Тип предохранительного клапана",
                    'description': "",
                    'visibility': True,
                    'required_type':  "list",
                    "all_values": all_type_names
                }

                # res = [debug_param, mixture, envs_values, climate_values, type_values]
                res.append(type_values)

            #валидация нужна
            elif type_val not in all_type_names:
            
                
                type_values = {
                    'id': 3,
                    'name': "Тип предохранительного клапана",
                    'description': "",
                    'visibility': True,
                    'required_type':  "list",
                    "all_values": all_type_names,
                    "response_value" : type_val,
                    "error" : "Надо выбрать один из предложеннных вариантов"
                }

                # res = [debug_param, mixture, envs_values, climate_values, type_values]
                res.append(type_values)

            #собрал тип клапана
            else:
                type_values = {
                    'id': 3,
                    'name': "Тип предохранительного клапана",
                    'description': "",
                    'visibility': True,
                    'required_type':  "list",
                    "all_values": all_type_names,
                    "response_value" : type_val
                }
                res.append(type_values)
                got_type = True

        #Температура
        if got_type:
            # задана пользователем?
            # T_param  = self._get_param_by_name("Температура рабочей среды", select_formula_params)
            T_param  = [value for param_name, value in select_formula_params.items() if param_name == "Температура рабочей среды"]
            T = int(T_param[0]) if T_param else None

            #если нет
            if T is None:
                #создать
                T_values = {
                    'id': 4,
                    'name': "Температура рабочей среды",
                    'description': "Ввведите значение температуры рабочей среды (°C)",
                    'visibility': True,
                    'required_type':  "user_input"
                }

                # res = [debug_param, mixture, envs_values, climate_values, type_values, T_values]
                res.append(T_values)
            
            #валидировать:
            elif (type_val == "Пружинный (В)" and (T < -60 or T > 600) ) or (type_val == "Пилотный (П)" and (T < -60 or T > 250) ):
                T_values = {
                    'id': 4,
                    'name': "Температура рабочей среды",
                    'description': "Ввведите значение температуры рабочей среды (°C)",
                    'visibility': True,
                    'required_type':  "user_input",
                    "response_value" : T,
                    "error" : "Температура должна быть в диапазоне от -60°С до 600°С для пружинных и от -60°С до 250°С для пилотных клапанов"
                }

                # res = [debug_param, mixture, envs_values, climate_values, type_values, T_values]
                res.append(T_values)
            
            else:
                T_values = {
                    'id': 4,
                    'name': "Температура рабочей среды",
                    'description': "Ввведите значение температуры рабочей среды (°C)",
                    'visibility': True,
                    'required_type':  "user_input",
                    "response_value" : T
                }

                got_T = True
                #ПОТОМ УДАЛИ
                # res = [debug_param, mixture, envs_values, climate_values, type_values, T_values]
                res.append(T_values)

        ################# РАСЧЕТ #################
        if got_T:
            #ключи === названия колонок БД
            searching_table_name = "reguljator_table"

            #чтобы проще было заполнять
            # all_columns_names = await db.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = \'{searching_table_name}\';"))
            # rows_all_columns_names = [row.column_name for row in all_columns_names]
            # print("Список колонок таблицы: ", rows_all_columns_names)
        

            env_keys = {
                "name" : "nazvanie_rabochej_sredy",
                "environment" : "agregatnoe_sostojanie",
                "molecular_weight" : "molekuljarnaja_massa",
                "density" : "plotnost_zhidkosti",
                # "density_ns": "",
                "material" : "material",
                "viscosity" : "vjazkost_pa_s",
                "isobaric_capacity" : "udel_naja_izobarnaja_teploemkost_kdzh_kg_k",
                "molar_mass" : "moljarnaja_massa",
                "isochoric_capacity" : "udel_naja_izohornaja_teploemkost_kdzh_kg_k",
                "adiabatic_index" : "pokazatel_adiabaty",
                "compressibility_factor" : "faktor_szhimaemosti",
            }
            #собрать список параметров сред
            envs_json = []
            env_type = set()

            env_name_colunm = env_keys["name"]

            for env in envs:
                env_name = list(env.keys())[0]
                r = env[env_name]
                ###################### собрать sql запрос ##############################
                env_params_sql = "SELECT "
                for keys in env_keys.keys():
                    colunm_name = env_keys[keys]
                    env_params_sql += colunm_name + ", "
                env_params_sql = env_params_sql[:-2]
                env_params_sql += f" FROM {searching_table_name} WHERE {env_name_colunm} = \'{env_name}\';"
                # print(env_params_sql)
                sql_result = await db.execute( text(env_params_sql) )
                env_result = sql_result.mappings().first()
                # print(env_result.name)
                ###################### обработать его в json ###########################
                env_json = {
                    "name" : env_result.nazvanie_rabochej_sredy,
                    "r" : r,
                    "environment" : env_result.agregatnoe_sostojanie,
                    "molecular_weight" : env_result.molekuljarnaja_massa,
                    "density" : env_result.plotnost_zhidkosti,
                    "material" : env_result.material,
                    "viscosity" : env_result.vjazkost_pa_s,
                    "isobaric_capacity" : env_result.udel_naja_izobarnaja_teploemkost_kdzh_kg_k,
                    "molar_mass" : env_result.moljarnaja_massa,
                    "isochoric_capacity" : env_result.udel_naja_izohornaja_teploemkost_kdzh_kg_k,
                    "adiabatic_index" : env_result.pokazatel_adiabaty,
                    "compressibility_factor" : env_result.faktor_szhimaemosti,
                }

                #возможные типы состава сред
                env_type.add(env_json["environment"])

                #значения для ключей среды
                envs_json.append(env_json)

            result = {
                "name" : "",
                "environment" : "",
                "molecular_weight" : 0,
                "density" : 0,
                "density_ns": 0,
                "material" : "",
                "viscosity" : 0,
                "isobaric_capacity" : 0,
                "molar_mass" : 0,
                "isochoric_capacity" : 0,
                "adiabatic_index" : 0,
                "compressibility_factor" : 1,
            }
            r_max = 0
            if len(env_type) == 1:
                env_type = f"Однородная смесь - {list(env_type)[0]}"
                result["environment"] = env_type

                if list(env_type)[0] == "Жидкость":
                    ch_den = 0
                    zn_den = 0
                    pre_viscosity = 0
                    for env in envs_json:
                        r = env["r"]
                        result["name"] += f"{env['name']}:{r}% "
                        result["molecular_weight"] += float(env["molecular_weight"]) * r
                        ch_den += float(env["density"]) * r
                        zn_den += r
                        pre_viscosity += log10(float(env["viscosity"])) * r


                    result["density"] = ch_den/zn_den
                    result["density_ns"] = result["density"]
                    result["viscosity"] = 10**(pre_viscosity)

                elif list(env_type)[0] == "Газ": #если среда - газ
                    viscosity_сh = 0
                    viscosity_zn = 0
                    pre_M = 0
                    adiabatic_index = 0
                    adiabatic_index_zn = 0
                    for env in envs_json:
                        r = env["r"]
                        result["name"] += f"{env['name']}:{r}% "
                        M_i = float(env["molar_mass"])
                        u_i = float(env["viscosity"])
                        pre_M += M_i * r
                        viscosity_сh += u_i * r * sqrt(M_i)
                        viscosity_zn += r * sqrt(M_i)
                        adiabatic_index += float(env['adiabatic_index']) * r

                        # плотность при н.у.
                        result["density"] += (M_i * r)
                        result["molar_mass"] = pre_M #/100
                        result["viscosity"] = viscosity_сh / viscosity_zn
                        result["adiabatic_index"] = adiabatic_index

                        # плотность при н.у.
                        result["density"] = result["density"] / 22.4
            else:
                result["environment"] = "Неоднородная смесь"
                density_ch = 0
                density_zn = 0
                pre_u = 0
                for env in envs_json:

                    r = env["r"]
                    result["name"] += f"{env['name']}:{r}% "

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
                        result["density_ns"] = density_ch / density_zn

                #рабочая плотность
                result["density"] = density_ch / density_zn
                result["viscosity"] = pre_u

                material = []
            
            material = []
            for env in envs_json:
                if ( env['name'] == 'Сероводород' and env["r"] < 0.06 ) and result["environment"] == "Смесь":
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

            ########### ЗАПОЛНИТЬ ПАРАМЕТРЫ ##########
            param_result_dict = {
                "name" : "",
                "environment" : "",
                "molecular_weight" : "",
                "density" : "",
                "material" : "",
                "viscosity" : "",
                "isobaric_capacity" : "",
                "molar_mass" : "",
                "isochoric_capacity" : "",
                "adiabatic_index" : "",
                "compressibility_factor" : "",
            }
            for i, param_key in enumerate(result.keys()): 
                param = {
                    'id': i+4,
                    'name': param_key,
                    'description': "",
                    'visibility': False,
                    'required_type':  "list",
                    "response_value" : result[param_key]
                }
                res.append(param)

        

        return {"total_change" : res}

def mixture(envs : list, climate : str, T : float):
    result = {
        "name" : "",
        "environment" : "",
        "molecular_weight" : 0,
        "density" : 0,
        "density_ns": 0,
        "material" : "",
        "viscosity" : 0,
        "isobaric_capacity" : 0,
        "molar_mass" : 0,
        "isochoric_capacity" : 0,
        "adiabatic_index" : 0,
        "compressibility_factor" : 1,
    }

    


    r_max = 0
    #проверка типа среды смеси
    if len(env_type) == 1: #если среда однородная
        result["environment"] = env_type.pop()
        if result["environment"] == "Жидкость": #если среда - жидкость
            ch_den = 0
            zn_den = 0
            pre_viscosity = 0
            for env in envs:
                r = env["r"]
                result["name"] += f"{env['name']}:{r*100}% "
                result["molecular_weight"] += env["molecular_weight"] * r
                ch_den += env["density"] * r
                zn_den += r
                pre_viscosity += log10(env["viscosity"]) * r

                '''
                if r > r_max:
                    # Плотность несущей среды
                    r_max = r
                    result["density_ns"] = env["density"]
                '''


            result["density"] = ch_den/zn_den
            result["density_ns"] = result["density"]
            result["viscosity"] = 10**(pre_viscosity)
            
            '''
            #добавить подбор материала result["material"]
            if "Морская вода" in result["name"]:
                result["material"] = "12Х18Н12М3ТЛ"
            elif ("Масло подсолнечное" in result["name"]) or ("Лимонная кислота" in result["name"]) or ("Молочная кислота" in result["name"]):
                result["material"] = "12Х18Н9ТЛ"
            '''

        elif result["environment"] == "Газ": #если среда - газ
            viscosity_сh = 0
            viscosity_zn = 0
            pre_M = 0
            adiabatic_index = 0
            adiabatic_index_zn = 0
            density_ns_zn = 0
            for env in envs:
                r = env["r"]
                result["name"] += f"{env['name']}:{r*100}% "
                M_i = env["molar_mass"]
                u_i = env["viscosity"]
                pre_M += M_i * r
                viscosity_сh += u_i * r * sqrt(M_i)
                viscosity_zn += r * sqrt(M_i)
                adiabatic_index += env['adiabatic_index'] * r

                # плотность при н.у.
                result["density_ns"] += (M_i * r)
                #density_ns_zn += r
                '''
                if r > r_max:
                    # Плотность несущей среды
                    r_max = r
                    result["density_ns"] = ((env["molar_mass"] / 22.4) * r) / r
                '''
                
            result["molar_mass"] = pre_M #/100
            result["viscosity"] = viscosity_сh / viscosity_zn
            result["adiabatic_index"] = adiabatic_index

            # плотность при н.у.
            result["density_ns"] = result["density_ns"] / 22.4
            result["density"] = None
            #result["density"] = result["density_ns"] * (273.15) / (T + 273.15)

            print()

    else:
        result["environment"] = "Смесь"
        density_ch = 0
        density_zn = 0
        pre_u = 0
        for env in envs:

            r = env["r"]
            result["name"] += f"{env['name']}:{r*100}% "

            # pre_viscosity += log10(env["viscosity"]) * r

            if env["environment"] == "Газ":
                M = env["molar_mass"]
                density_ch += (env["molar_mass"] / 22.4) * r
                density_zn += r
            elif env["environment"] == "Жидкость":
                M = env["molecular_weight"]
                density_ch += env["density"] * r
                density_zn += r

            pre_u += r * env["viscosity"] * M

            if r > r_max:
                # Плотность несущей среды при нормальных условиях
                r_max = r
                result["density_ns"] = density_ch / density_zn

        #рабочая плотность
        result["density"] = density_ch / density_zn
        result["viscosity"] = pre_u
        # result["viscosity"] = 10**(pre_viscosity)

    material = []
    for env in envs:
        if env['name'] == 'Сероводород' and r < 0.06 and result["environment"] == "Смесь":
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

    result["T"] = T

    return result

ALLOWED_FUNCTIONS =  [method for method in dir(CodeParametr) if callable(getattr(CodeParametr, method)) and not method.startswith("__")]