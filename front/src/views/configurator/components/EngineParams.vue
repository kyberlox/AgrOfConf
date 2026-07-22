<template>
<div class="flex flex-row justify-between items-center">
    <div class="text-[16px] font-[600]">
        Выберите параметры
    </div>
    <div class="flex flex-row gap-[4px] items-center">
        <RequiredIcon />
        <div>— обязательные поля</div>
    </div>
</div>
<div class="border border-[#EAECEF] w-full h-[1px] col-span-full"></div>
<div class="grid gap-[25px] items-end"
     :class="`grid-cols-${gridCols}`">
    <template v-for="(param, index) in renderData.filter(e => (e as IFormattedData).visibility && (e as IFormattedData).required_type !== 'raschet' && ((e as IFormattedData).required_type == 'select-input' ? (e as IFormattedData).all_values : true))"
              :key="'formParam' + param.name">
        <div v-if="param.name == 'sep' && index !== 0"
             class="divider">
        </div>
        <!-- Смежный селект + инпут для сред -->
        <SelectInput v-else-if="(param as IFormattedData).required_type == 'select-input'"
                     :param="(param as IFormattedData)"
                     @changeSelectInputValue="(value) => $emit('valueChanged', value, param.name)" />

        <!-- свободный текстовый инпут -->
        <BaseInput v-else-if="(param as IFormattedData).required_type == 'user_input'"
                   :propsClass="'input-param'"
                   :props-placeholder="'Впишите значение'"
                   :propsName="param.name + (index + 1)"
                   :props-label="param.name"
                   :error="'error' in param ? param.error : ''"
                   @valueChanged="(value: string | null) => $emit('valueChanged', value ?? '', param.name)" />

        <!-- выпадающий список -->
        <BaseSelect v-else-if="(param.name !== 'sep')"
                    :propsLabel="param.name"
                    :propsId="param.name"
                    :propsClass="'paramsSelect'"
                    :propsValue="(param as IFormattedData).response_value ? String((param as IFormattedData).response_value) : ''"
                    :propsOptions="checkParams(param as IFormattedData)"
                    :propsPlaceholder="!(param as IFormattedData).filtered_values?.length && 'filtered_values' in param ? '' : 'Выберите значение'"
                    :needReq="true"
                    :labelIcon="createLabelIconsComponent(param as IFormattedData, () => console.log('testComp'))"
                    :error="'error' in param ? param.error : ''"
                    :errorIcon="AlertCircle"
                    :disabled="((!(param as IFormattedData).filtered_values?.length && 'filtered_values' in param) || (param as IFormattedData).filtered_values?.includes('нет')) && type == 'auto'"
                    @valueChanged="(value: string) => $emit('valueChanged', value, param.name)" />


    </template>
</div>
</template>

<script lang='ts'>
import { defineComponent, computed } from 'vue';
import ParamsHeaderIcons from './ParamsHeaderIcons.vue';
import type { IFormattedData } from '@/assets/interfaces/IForm';
import { createLabelIconsComponent } from '@/composables/createComponent';
import AlertCircle from '@/assets/icons/AlertCircle.svg?component';
import { useWindowSize } from '@vueuse/core'
import RequiredIcon from '@/assets/icons/RequiredIcon.svg?component';
import SelectInput from '@/components/SelectInput.vue';
import { BaseInput, BaseSelect } from 'beans-ui-kit';
import { screenMixins } from '@/assets/static/screenMixins';
import { useConfiguratorStore } from '@/stores/configurator.ts';

export default defineComponent({
    components: {
        BaseSelect,
        ParamsHeaderIcons,
        AlertCircle,
        RequiredIcon,
        SelectInput,
        BaseInput,
    },
    props: {
        form: {
            type: Array<IFormattedData>,
            requied: true
        },
        type: {
            type: String,
            default: 'auto'
        }
    },
    emits: ['valueChanged'],
    setup(props) {
        const { width } = useWindowSize();
        const configurator = useConfiguratorStore();
        const freeConfigMode = computed(() => configurator.getFreeModeConfig);

        const gridCols = computed(() => width.value < screenMixins.md ? 1 : width.value < screenMixins.lg ? 2 : 3);
        const renderData = computed(() => {
            const rows: Array<IFormattedData | { name: string }> = [];
            if (!props.form) return rows;
            let count = 0;
            props.form.forEach((e) => {
                if (count < gridCols.value) {
                    rows.push(e);
                    count++;
                }
                else {
                    rows.push({ name: 'sep' } as { name: string }, e)
                    count = 1;
                }
            })
            return rows
        })

        const checkParams = (param: IFormattedData) => {
            switch (freeConfigMode.value) {
                case true:
                    return Array.from(param?.all_values) || []

                case false:
                    return Array.from((!('filtered_values' in param) || !param?.filtered_values) ?
                        param?.all_values :
                        param?.filtered_values || [])

                default:
                    return []
            }
        }

        return {
            AlertCircle,
            gridCols,
            renderData,
            freeConfigMode,
            createLabelIconsComponent,
            checkParams,
        }
    }
});
</script>