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
<div class="border border-[#EAECEF] w-full h-[1px] col-span-full m-auto"></div>
<div class="grid gap-x-[16px] gap-y-[24px] items-end"
     :class="`grid-cols-${gridCols}`">
    <template v-for="(param, index) in renderData.filter(e => (e as IFormattedData).visibility || (e as IFormattedData).visibility == null)"
              :key="'formParam' + param.name + index">
        <div v-if="param.name == 'sep' && index !== 0"
             class="border border-[#EAECEF] w-full h-[1px] col-span-full m-auto">
        </div>
        <!-- Смежный селект + инпут для сред -->
        <SelectInput v-else-if="(param as IFormattedData).required_type == 'select-input'"
                     :param="(param as IFormattedData)"
                     @changeSelectInputValue="(value) => $emit('valueChanged', value, param.name)" />

        <!-- свободный текстовый инпут -->
        <BaseInput v-else-if="(param as IFormattedData).required_type == 'user_input'"
                   :propsClass="'input-param'"
                   :props-placeholder="(param as IFormattedData).description ?? ''"
                   :propsName="param.name + (index + 1)"
                   :props-label="param.name"
                   :error="'error' in param ? param.error : ''"
                   @valueChanged="(value: string) => $emit('valueChanged', Number(value), param.name)" />

        <!-- выпадающий список -->
        <BaseSelect v-else-if="(param.name !== 'sep')"
                    :propsLabel="param.name"
                    :propsClass="'paramsSelect'"
                    :propsValue="(param as IFormattedData).response_value ? String((param as IFormattedData).response_value) : ''"
                    :propsOptions="switchOptions(param as IFormattedData)"
                    :propsPlaceholder="!(param as IFormattedData).filtered_values?.length && 'filtered_values' in param ? '' : 'Выберите значение'"
                    :markedOptions="'filtered_values' in param && Array.isArray(param.filtered_values) ? param.filtered_values : typeof (param as IFormattedData).filtered_values == 'string' ? [(param as IFormattedData).filtered_values] : []"
                    :needReq="true"
                    :labelIcon="createLabelIconsComponent(param as IFormattedData, () => console.log('abob'))"
                    :error="'error' in param ? param.error : ''"
                    :errorIcon="AlertCircle"
                    :disabled="(!(param as IFormattedData).filtered_values?.length && 'filtered_values' in param) || (param as IFormattedData).filtered_values?.includes('нет')"
                    @valueChanged="(value: string) => $emit('valueChanged', value, param.name)" />
    </template>
</div>
</template>

<script lang='ts'>
import { BaseSelect } from 'beans-ui-kit';
import { defineComponent, h, ref, computed, render, watchEffect } from 'vue';
import ParamsHeaderIcons from './ParamsHeaderIcons.vue';
import type { IFormattedData } from '@/assets/interfaces/IForm';
import { createLabelIconsComponent } from '@/composables/createComponent';
import AlertCircle from '@/assets/icons/AlertCircle.svg?component';
import { useWindowSize } from '@vueuse/core'
import RequiredIcon from '@/assets/icons/RequiredIcon.svg?component';
import SelectInput from '@/components/SelectInput.vue';
import { BaseInput } from 'beans-ui-kit';

export default defineComponent({
    components: {
        BaseSelect,
        ParamsHeaderIcons,
        AlertCircle,
        RequiredIcon,
        SelectInput,
        BaseInput
    },
    props: {
        form: {
            type: Array<IFormattedData>,
            requied: true
        }
    },
    emits: ['valueChanged'],
    setup(props) {
        const { width } = useWindowSize()
        const gridCols = computed(() => width.value < 992 ? 2 : width.value < 1200 ? 3 : 4);
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
                    rows.push({ name: 'sep' } as { name: string });
                    rows.push(e)
                    count = 1;
                }
            })
            return rows
        })

        const switchOptions = (param: IFormattedData) => {
            if (param.response_value || !('filtered_values' in param)) {
                console.log('1')
                return Array.isArray(param.all_values) ? param.all_values : [param.all_values];
            }
            else if ('filtered_values' in param && param.filtered_values?.length && !param.response_value) {
                console.log(2)
                return Array.isArray(param.filtered_values) ? param.filtered_values : [param.filtered_values];
            }
            else if (typeof param.filtered_values == 'string') {
                console.log(3)
                return [param.filtered_values];
            }
            else {
                return []
            }
        }

        return {
            AlertCircle,
            gridCols,
            renderData,
            h,
            createLabelIconsComponent,
            switchOptions
        }
    }
});
</script>