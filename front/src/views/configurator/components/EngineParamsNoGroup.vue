<template>
<div class="grid grid-cols-4 gap-x-[12px] gap-y-[16px]">
    <div v-for="(param, index) in items"
         :key="param.id"
         class="px-[10px] hover:none flex flex-row">
        <!-- Смежный селект + инпут для сред (кроме параметра-состава смеси) -->
        <SelectInput v-if="(param as IFormattedData).required_type == 'select-input' && (param as IFormattedData).type !== 'FormulaMix' && (param as IFormattedData).name != 'Состав смеси'"
                     :param="(param as IFormattedData)"
                     :disabled="paramsLoading"
                     @changeSelectInputValue="(value) => $emit('valueChanged', value, param.name)" />

        <!-- Редактор состава смеси (type='FormulaMix' или имя «Состав смеси»): попап по клику на параметр -->
        <MixtureEditor v-else-if="(param as IFormattedData).type == 'FormulaMix' || (param as IFormattedData).name == 'Состав смеси'"
                       :param="(param as IFormattedData)"
                       :model-value="(userParams && userParams[param.name as keyof typeof userParams] && Array.isArray(userParams[param.name as keyof typeof userParams])) ? (userParams[param.name as keyof typeof userParams] as Array<{ [key: string]: number }>) : []"
                       :disabled="paramsLoading"
                       @valueChanged="(value: Array<{ [key: string]: number }>) => $emit('valueChanged', value, param.name)" />

        <!-- Чекбокс (например, включение расчёта смеси) -->
        <CheckboxInput v-else-if="(param as IFormattedData).required_type == 'checkbox'"
                       :param="(param as IFormattedData)"
                       :model-value="!!(userParams && userParams[param.name as keyof typeof userParams])"
                       :disabled="paramsLoading"
                       @valueChanged="(value: boolean) => $emit('valueChanged', value, param.name)" />

        <!-- свободный текстовый инпут -->
        <BaseInput v-else-if="(param as IFormattedData).required_type == 'user_input'"
                   :class="{ 'input-param__wrapper--no-response': (userParams && !userParams[param.name as keyof typeof userParams]) }"
                   :inputSettings="initInputSettings(param, index)"
                   @valueChanged="(value: string | null) => $emit('valueChanged', value ?? '', param.name)" />

        <!-- выпадающий список -->
        <BaseSelect v-else
                    :class="{ 'select-params__wrapper--no-response': (userParams && !userParams[param.name as keyof typeof userParams]) }"
                    :selectSettings="initSelectSettings(param)"
                    @valueChanged="(value: string) => $emit('valueChanged', value, param.name)" />

        <!-- Статус вопроса -->
        <QuestionStatus v-if="type == 'auto'"
                        :status="paramsLoading ? 'loading' : param.error ? 'canceled' : param.response_value ? 'checked' : ''"
                        @resetValue="$emit('resetValue', param.name)" />
    </div>
</div>
</template>
<script lang='ts'>
import type { IFormattedData } from '@/assets/interfaces/IForm';
import { defineComponent, type PropType, computed } from 'vue';
import { BaseButton, BaseInput, BaseSelect } from 'beans-ui-kit';
import SelectInput from '@/components/SelectInput.vue';
import CheckboxInput from '@/components/CheckboxInput.vue';
import MixtureEditor from '@/components/MixtureEditor.vue';
import { useConfiguratorStore } from '@/stores/configurator';
import { createLabelIconsComponent } from '@/composables/createComponent';
import AlertCircle from '@/assets/icons/AlertCircle.svg?component';
import QuestionStatus from '@/components/layout/QuestionStatus.vue';
import { replaceSpotOrComma } from '@/utils/replaceSpotOrComma';

export default defineComponent({
    components: {
        BaseButton,
        BaseSelect,
        BaseInput,
        SelectInput,
        CheckboxInput,
        MixtureEditor,
        QuestionStatus,
        AlertCircle
    },
    emits: ['valueChanged', 'resetValue'],
    props: {
        items: {
            type: Array as PropType<IFormattedData[]>,
            required: true
        },
        gridCols: {
            type: Number,
            required: true
        },
        type: {
            type: String,
            default: 'auto'
        },
        paramsLoading: {
            type: Boolean,
            default: false
        },
        userParams: {
            type: Object as PropType<Record<string, string | boolean | Array<{ [key: string]: number }>>>
        }
    },
    setup(props) {
        const freeConfigMode = computed(() => configurator.getFreeModeConfig);
        const configurator = useConfiguratorStore();

        const checkParams = (param: IFormattedData) => {
            switch (freeConfigMode.value) {
                case true:
                    return Array.from(param?.all_values.map(e => replaceSpotOrComma(e, 'spot'))) || []

                case false:
                    return Array.from((!('filtered_values' in param) || !param?.filtered_values || param.response_value) ?
                        (param?.all_values.map(e => replaceSpotOrComma(e, 'spot'))) :
                        (param?.filtered_values.map(e => replaceSpotOrComma(e, 'spot'))) || [])
                default:
                    return []
            }
        }

        type keyofUserParams = keyof typeof props.userParams;
        const setPropsValue = (param: IFormattedData): string => {
            const raw = props.userParams ? props.userParams[param.name as keyofUserParams] : undefined;
            // Значения-массивы (состав смеси) и булевы (чекбокс) обрабатываются
            // отдельными компонентами и сюда не попадают, но приводим их к строке
            // для type-безопасности.
            const value = Array.isArray(raw) || typeof raw === 'boolean'
                ? String(raw)
                : raw
            if (value) {
                return replaceSpotOrComma(value, 'spot') || ''
            }
            else if (param?.response_value)
                return replaceSpotOrComma(param?.response_value, 'spot') || ''
            else return ''
        }

        const initSelectSettings = (param: IFormattedData) => {
            return {
                label: param.name,
                id: param.name,
                class: 'select-params--no-group',
                value: setPropsValue(param),
                options: checkParams(param),
                placeholder: !param.filtered_values?.length && 'filtered_values' in param ? '' : 'Выберите значение',
                needReq: true,
                labelIcon: createLabelIconsComponent(param, () => console.log('testComp')),
                error: 'error' in param ? param.error : '',
                errorIcon: AlertCircle,
                disabled: (((!param.filtered_values?.length && 'filtered_values' in param) || (param as IFormattedData).filtered_values?.includes('нет')) && props.type == 'auto') || props.paramsLoading
            }
        }

        const initInputSettings = (param: IFormattedData, index: number | string) => {
            return {
                class: 'input-param--no-group',
                placeholder: props.paramsLoading ? '...' : 'Впишите значение',
                value: setPropsValue(param),
                name: param.name + (Number(index) + 1),
                label: param.name,
                error: 'error' in param ? (param as IFormattedData).error : '',
                disabled: props.paramsLoading
            }
        }

        return {
            freeConfigMode,
            AlertCircle,
            setPropsValue,
            createLabelIconsComponent,
            checkParams,
            initSelectSettings,
            initInputSettings
        }
    }
});
</script>