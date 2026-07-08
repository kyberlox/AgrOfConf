<template>
<div class="flex items-center ">
    <span :class="[
        'truncate max-w-[120px] inline-block',
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
            // debugger
            const rawValue = props.params.value;
            if (rawValue === undefined || rawValue === null || rawValue === 'undefined' || rawValue === 'Не определено') {
                return 'Не определено1';
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