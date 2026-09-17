import { ref, computed, type Ref } from 'vue';
import { replaceSpotOrComma } from "@/utils/replaceSpotOrComma";
import Api from '@/utils/Api';
import type { IFormattedData, userParams } from '@/assets/interfaces/IForm';
import { clone } from 'chart.js/helpers';
import type { configuratorStoreType } from '@/stores/configurator';
import { arraysEqual } from '@/utils/arrayUtil';

interface IConfiguratorDeps {
    userInputs: Ref<userParams>,
    freeConfigMode: Ref<boolean>,
    priorityParam: Ref<string>,
    manuallyChanged: Ref<Record<string, boolean>>,
    form: Ref<IFormattedData[]>,
    mixtureCompositionName: Ref<string>,
    productName: Ref<string>,
    rerunGuard: Ref<boolean>,
    productId: string,
    configuratorStore: configuratorStoreType,
    paramsLoading: Ref<boolean>
}

let abortController: AbortController | null = null;
export const useConfiguratorForm = (deps: IConfiguratorDeps) => {
    const {
        userInputs,
        freeConfigMode,
        priorityParam,
        manuallyChanged,
        form,
        mixtureCompositionName,
        productName,
        rerunGuard,
        productId,
        configuratorStore,
        paramsLoading
    } = deps

    const prepareBody = (body: userParams) => {
        if (abortController) {
            abortController.abort();
        }
        let newBody: userParams = clone(body);
        if (freeConfigMode && Object.keys(newBody).length) {
            return
        }
        if (newBody && Object.keys(newBody).length) {
            Object.keys(newBody)?.forEach((key, index) => {
                if (!Array.isArray(newBody[key]) && typeof newBody[key] !== 'boolean') {
                    newBody[key] = replaceSpotOrComma(newBody[key]!, 'comma');
                }
                if (priorityParam.value && typeof priorityParam.value == 'string')
                    newBody.priority = priorityParam.value;
            })
        }
    }

    const paramsUpdateRequest = async (body: userParams) => {
        prepareBody(body)
        abortController = new AbortController();
        const signal = abortController.signal;
        try {
            paramsLoading.value = true;
            const data = await Api.post(`/module_search/process_table_data?product_id=${productId}`, body, {}, signal)
            if (data?.files) {
                configuratorStore.setDocs(data.files)
            }
            const errors: string[] = [];
            let answeredCounter = 0;
            let questionCounter = 0;
            if (!data || !('parameters' in data) || !data.parameters.length) return
            data.parameters.forEach((e: IFormattedData) => {
                if (e.name == 'Маркировка' && e.response_value) {
                    configuratorStore.setMark(e.response_value as string)
                }
                if ('error' in e && e.error) {
                    errors.push(e.error)
                }
                if ('response_value' in e && (typeof e.response_value !== 'object') && userInputs.value[e.name] !== e.response_value) {
                    userInputs.value[e.name] = e.response_value;
                    answeredCounter++
                } else if (e.response_value == null) {
                    delete userInputs.value[e.name]
                }
                questionCounter++
            })
            // Параметры, которые сервер пометил как ошибочные, стали несовместимыми
            // с текущим выбором. Убираем их из списка явных выборов, чтобы их старое
            // значение не продолжало отправляться и не блокировало подбор — тогда
            // остальные параметры смогут автоматически «подстроиться» под новый выбор.
            // Исключение — ошибки валидации (is_validation): это явный ввод пользователя
            // (например, температура вне диапазона), такие параметры НЕ удаляем и ошибку
            // показываем в блоке подсказки, чтобы пользователь мог её исправить.
            let removedError = false;
            data.parameters.forEach((e: IFormattedData) => {
                if ('error' in e && e.error && !e.is_validation) {
                    if (e.name in userInputs.value) {
                        delete userInputs.value[e.name]
                        removedError = true
                    }
                    delete manuallyChanged.value[e.name]
                }
            })
            configuratorStore.setCalcParams(data.parameters.filter((e: IFormattedData) => (e.required_type == 'raschet' || e.required_type == 'drawing') && e.response_value));
            configuratorStore.setCovered(Number(answeredCounter));
            configuratorStore.setAllQuestions(Number(questionCounter));
            if (errors.length) {
                configuratorStore.setError(errors)
            }
            else configuratorStore.setDefaultError()

            if (!(data && 'parameters' in data)) return
            form.value = data.parameters
            const mixtureParam = data.parameters.find((e: IFormattedData) => e.type === 'FormulaMix' || e.name === 'Состав смеси')
            if (mixtureParam) mixtureCompositionName.value = mixtureParam.name
            productName.value = data.product_name

            // Были удалены ошибочные (несовместимые) параметры — пересчитываем
            // подбор без них, чтобы сервер автоматически подставил единственные
            // доступные значения и зависимые параметры адаптировались.
            if (removedError && !rerunGuard.value) {
                rerunGuard.value = true
                await paramsUpdateRequest(userInputs.value)
            }
        } finally {
            rerunGuard.value = false
            paramsLoading.value = false
        }
    }
    const handleValueChanged = (value: string, key: keyof typeof userInputs.value) => {
        // Сброс значения (resetValue): убираем параметр из явных выборов и
        // перезапрашиваем подбор без него, чтобы зависимые параметры пересчитались.
        if (value == null) {
            delete userInputs.value[key];
            delete manuallyChanged.value[key];
            paramsUpdateRequest(userInputs.value);
            return;
        }
        // Select-input (состав смеси) приходит массивом {среда: доля}.
        // Конвертация в строку через replaceSpotOrComma сломает JSON — не трогаем.
        // Чекбокс приходит boolean (True/False) — тоже не конвертируем.
        const prepared = Array.isArray(value) || typeof value === 'boolean'
            ? value
            : replaceSpotOrComma(value, 'spot') || '';
        const shouldProcess = Array.isArray(value) || typeof value === 'boolean'
            ? userInputs.value[key] !== prepared
            : value && userInputs.value[key] !== prepared;

        if (shouldProcess) {
            userInputs.value[key] = prepared;
            // Помечаем как явный выбор пользователя — такой параметр не будет
            // перезаписан авто-подстановкой и останется в приоритете.
            manuallyChanged.value[String(key)] = true;
            priorityParam.value = String(key);
            // При выключении чекбокса «Смесь»: очищаем связанные параметры,
            // чтобы они не оставались в выборе и не отправлялись на сервер.
            if (key === 'Смесь' && typeof prepared == 'boolean' && prepared === false) {
                delete userInputs.value['Тип смеси'];
                delete manuallyChanged.value['Тип смеси'];
                if (mixtureCompositionName.value) {
                    delete userInputs.value[mixtureCompositionName.value];
                    delete manuallyChanged.value[mixtureCompositionName.value];
                }
            }
            // При смене типа смеси: очищаем состав, т.к. список сред мог измениться.
            if (key === 'Тип смеси' && mixtureCompositionName.value && userInputs.value[mixtureCompositionName.value] !== undefined) {
                delete userInputs.value[mixtureCompositionName.value];
                delete manuallyChanged.value[mixtureCompositionName.value];
            }
            if (!userInputs.value) {
                paramsUpdateRequest({})
            }
        }
    }

    const checkForNeedUpdate = () => {
        if (Object.keys(userInputs.value).length) {
            let shouldSend = false;
            for (const [key, current] of Object.entries(userInputs.value)) {
                const formTarget = form.value.find(formEl => formEl.name == key)
                const serverValue = formTarget?.response_value
                // Параметр-состав смеси (select-input) — массив {среда: доля}: сравниваем
                // по содержимому, а не по ссылке — сервер каждый раз присваивает
                // новый объект. Если пользователь менял состав — отправляем.
                if (Array.isArray(current) || Array.isArray(serverValue)) {
                    if (!arraysEqual(current, serverValue)) {
                        shouldSend = true;
                        break;
                    }
                } else if (!serverValue || current !== serverValue) {
                    shouldSend = true;
                    break;
                }
            }
            if (shouldSend) return paramsUpdateRequest(userInputs.value)
        }
    }
    return {
        paramsUpdateRequest,
        handleValueChanged,
        checkForNeedUpdate
    }
}