<template>
<SlotModal>
    <div class="p-[80px] flex flex-col gap-[32px]">
        <span>Создание запроса</span>
        <div class="p-[32px] rounded-[16px] border border-(-color-information-gray-200)">
        </div>
    </div>
</SlotModal>
</template>
<script lang='ts'>
import { defineComponent, ref } from 'vue';
import SlotModal from '@/components/layout/SlotModal.vue';
import { BaseInput } from 'beans-ui-kit';

export default defineComponent({
    components: {
        SlotModal,
        BaseInput
    },
    props: {},
    setup() {
        const questionsStructure = ref(
            {
                name: '',
                organization: '',
                phone: '',
                inn: '',
                address: '',
                email: '',
                contacts: [{}],
            }
        );

        return {}
    }
});
</script>