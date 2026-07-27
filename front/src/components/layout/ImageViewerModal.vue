<template>
<SlotModal>
    <div class="rounded-[16px] p-[15px] hover:bg-gray-50 hover:border-gray-500 max-w-[80vh] ">
        <VueImageZoomer :regular="imageSrc"
                        hover-message="Наведите для приближения" />
    </div>
</SlotModal>
</template>
<script lang='ts'>
import { defineComponent } from 'vue';
import SlotModal from './SlotModal.vue';
import { VueImageZoomer } from 'vue-image-zoomer';

export default defineComponent({
    components: {
        SlotModal,
        VueImageZoomer
    },
    props: {
        imageSrc: {
            type: String
        }
    },
    setup() {
        return {

        }
    }
});
</script>