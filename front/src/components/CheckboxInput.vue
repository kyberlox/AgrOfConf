<template>
<div class="flex flex-col w-full gap-[4px] py-[6px] px-[4px]">
    <BaseCheckbox :propsClass="'checkbox'"
                  :propsLabel="param.name"
                  :propsStatus="checked"
                  :propsValue="param.name"
                  :disabled="disabled"
                  @valueChanged="(value: unknown, isChecked: boolean) => handleCheck(isChecked)" />
    <span v-if="'error' in param && param.error"
          class="text-[12px] text-red-500">{{ param.error }}</span>
</div>
</template>

<script lang='ts'>
import { defineComponent, type PropType, computed } from 'vue';
import { BaseCheckbox } from 'beans-ui-kit';
import type { IFormattedData } from '@/assets/interfaces/IForm';

export default defineComponent({
    components: {
        BaseCheckbox,
    },
    props: {
        param: {
            type: Object as PropType<IFormattedData>,
            required: true,
        },
        disabled: {
            type: Boolean,
            default: false,
        },
        modelValue: {
            type: Boolean,
            default: false,
        },
    },
    emits: ['valueChanged'],
    setup(props, { emit }) {
        const checked = computed<boolean>(() => {
            if (props.modelValue !== undefined && props.modelValue !== null) {
                return Boolean(props.modelValue);
            }
            return Boolean(props.param.response_value);
        });

        const handleCheck = (isChecked: boolean) => {
            emit('valueChanged', Boolean(isChecked));
        };

        return {
            checked,
            handleCheck,
        };
    },
});
</script>

<style scoped>
:deep(.checkbox) {
    margin-left: 12px;
}
</style>