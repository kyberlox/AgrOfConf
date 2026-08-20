<template>
<div class="grid grid-cols-1 ">
    <div v-for="(param, index) in items"
         :key="param.id"
         class="flex flex-row items-center px-[10px]  hover:bg-(--color-information-orange-50) ">
        <!-- Смежный селект + инпут для сред -->
        <SelectInput v-if="(param as IFormattedData).required_type == 'select-input'"
                     :param="(param as IFormattedData)"
                     :disabled="paramsLoading"
                     @changeSelectInputValue="(value) => $emit('valueChanged', value, param.name)" />

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
            type: Object as PropType<Record<string, string>>
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
            if (props.userParams && props.userParams[param.name as keyofUserParams]) {
                return replaceSpotOrComma(props.userParams[param.name as keyofUserParams]!, 'spot') || ''
            }
            else if (param?.response_value)
                return replaceSpotOrComma(param?.response_value, 'spot') || ''
            else return ''
        }

        const initSelectSettings = (param: IFormattedData) => {
            return {
                label: param.name,
                id: param.name,
                class: 'select-params',
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
                class: 'input-param',
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
