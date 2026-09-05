<template>
<SlotModal>
    <div class="flex flex-col gap-[15px] p-[15px] items-center justify-between">
        <div class="border border-gray-200 rounded-xl p-[15px] text-left w-[350px] max-w-[500px] flex flex-row items-center justify-between"
             v-for="(table, index) in tables"
             :key="index + 'productTable'">
            <span>{{ table }}</span>
            <div class="cursor-pointer text-red-500 hover:text-red-300 text-[14px] transform transition-all"
                 @click="$emit('deleteTable', table)">
                <TrashIcon />
            </div>
        </div>
    </div>
</SlotModal>
</template>
<script lang='ts'>
import SlotModal from '@/components/layout/SlotModal.vue';
import { defineComponent, type PropType } from 'vue';
import TrashIcon from '@/assets/icons/Trash.svg?component';

export default defineComponent({
    components: {
        SlotModal,
        TrashIcon
    },
    emits: ['deleteTable'],
    props: {
        tables: {
            type: Array as PropType<string[]>,
            required: true
        }
    },
    setup() {
        return {

        }
    }
});
</script>