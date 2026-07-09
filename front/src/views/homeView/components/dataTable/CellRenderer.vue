<template>
<div class="flex items-center">
    <span :class="[
        'truncate max-w-[200px] inline-block',
        isFirst ? 'underline cursor-pointer hover:text-orange-500 transition-colors duration-300' : ''
    ]">
        {{ displayValue }}
    </span>
</div>
</template>

<script lang="ts">
import { defineComponent, computed } from 'vue';

export default defineComponent({
    name: 'CellRenderer',
    props: {
        params: {
            type: Object,
            required: true
        }
    },
    setup(props) {
        const isFirst = computed(() => {
            const colDefs = props.params.colDefs || [];
            const fieldName = props.params.colDef?.field || '';
            return fieldName === colDefs[0];
        });

        const displayValue = computed(() => {
            const field = props.params.colDef?.field;
            const rawValue = props.params.value ?? (field ? props.params.data[field] : undefined);
            if (field == 'Шт.') {
                return '1'
            } else
                if (rawValue === undefined || rawValue === null || rawValue === 'undefined' || rawValue === 'Не определено') {
                    return 'Не определено';
                } else if (String(rawValue).includes(':')) {
                    return String(rawValue).split(' ')[0] || '';
                } else {
                    return String(rawValue);
                }
        });

        return {
            isFirst,
            displayValue
        };
    }
});
</script>