<template>
<SlotModal v-if="showDeleteModal">
    <div class="flex flex-col gap-2 p-4">
        <h1 class="mt-2">Вы уверены, что хотите удалить это изделие?</h1>
        <div class="flex flex-row justify-between mt-2">
            <BaseButton :props-class="'button-primary'"
                        @click.stop.prevent="$emit('closeAllModals')">Нет</BaseButton>
            <BaseButton :props-class="'button-primary'"
                        @click.stop.prevent="$emit('deleteProduct', product.id)">Да</BaseButton>
        </div>
    </div>
</SlotModal>
</template>
<script lang='ts'>
import { defineComponent, type PropType } from 'vue';
import { type IProduct } from '@/assets/interfaces/IProduct';
import { BaseButton } from 'beans-ui-kit';
import SlotModal from '@/components/layout/SlotModal.vue';

export default defineComponent({
    components: {
        BaseButton,
        SlotModal
    },
    props: {
        product: {
            type: Object as PropType<IProduct>,
            required: true
        },
        showDeleteModal: {
            type: Boolean,
            default: false
        }
    },
    emits: ['closeAllModals', 'deleteProduct'],
    setup() {
        return {}
    }
});
</script>