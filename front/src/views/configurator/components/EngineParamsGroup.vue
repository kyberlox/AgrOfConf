<template>
<div class="grid gap-[16px]"
     :class="`grid-cols-${gridCols}`">
    <template v-for="(param, index) in items"
              :key="param.id">
        <div :class="{ 'last:col-span-2': items.length % 2 }">
            <!-- Смежный селект + инпут для сред -->
            <SelectInput v-if="(param as IFormattedData).required_type == 'select-input'"
                         :param="(param as IFormattedData)"
                         :disabled="paramsLoading"
                         @changeSelectInputValue="(value) => $emit('valueChanged', value, param.name)" />

            <!-- свободный текстовый инпут -->
            <BaseInput v-else-if="(param as IFormattedData).required_type == 'user_input'"
                       :propsClass="'input-param'"
                       :props-placeholder="'Впишите значение'"
                       :propsName="param.name + (index + 1)"
                       :props-label="param.name"
                       :error="'error' in param ? (param as IFormattedData).error : ''"
                       :disabled="paramsLoading"
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
                        :error="'error' in param ? (param as IFormattedData).error : ''"
                        :errorIcon="AlertCircle"
                        :disabled="((!(param as IFormattedData).filtered_values?.length && 'filtered_values' in param) || (param as IFormattedData).filtered_values?.includes('нет')) && type == 'auto'"
                        @valueChanged="(value: string) => $emit('valueChanged', value, param.name)" />
        </div>
    </template>
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

export default defineComponent({
    components: {
        BaseButton,
        BaseSelect,
        BaseInput,
        SelectInput,
        AlertCircle
    },
    emits: ['valueChanged'],
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
        }
    },
    setup() {
        const freeConfigMode = computed(() => configurator.getFreeModeConfig);
        const configurator = useConfiguratorStore();

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
            freeConfigMode,
            AlertCircle,
            createLabelIconsComponent,
            checkParams
        }
    }
});
</script>
