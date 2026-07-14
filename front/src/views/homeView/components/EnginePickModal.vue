<template>
<div class="p-[80px] flex flex-col gap-[16px] w-max-content">
    <div class="flex flex-row items-center justify-between gap-[20px]">
        <h1 class="max-w-[160px]">
            Выберите изделие
        </h1>
    </div>
    <!-- Карточки приводов -->
    <div class="flex flex-col gap-[12px]">
        <div class="flex flex-row gap-[16px]">
            <RouterLink v-for="item in items"
                        :to="{ name: 'configurator', params: { id: item.id } }"
                        :key="'engine' + item.id"
                        class="w-[200px] h-[274] p-[17px] cursor-pointer flex flex-col gap-[10px] border border-[#EAECEF] rounded-[8px] hover:border-orange-500 duration-300 transition-all"
                        @click="$emit('selectEngine', item.id)">
                <div class=" w-full h-[170px] bg-contain bg-no-repeat bg-center"
                     :style="{ 'background-image': `url(http://agrofconf.emk.org.ru${item.image_url})` }">
                </div>
                <div class="text-[14px] text-(--text-primary)">
                    {{ item.name }}
                </div>
                <div class="text-[13px] text-(--text-secondary) text-[600]">
                    {{ item.manufacturer }}
                </div>
                <div class="text-[11px] text-(--text-secondary)">
                    {{ item.description }}
                </div>
            </RouterLink>
        </div>
    </div>
</div>
</template>
<script lang='ts'>
import { defineComponent, type PropType } from 'vue';
import type { IProduct } from '@/assets/interfaces/IProduct';
import UploadDocButton from '@/views/homeView/components/recognition/UploadDocButton.vue';
import PromptModal from './recognition/PromptModal.vue';

export default defineComponent({
    components: {
        UploadDocButton,
        PromptModal
    },
    props: {
        items: {
            type: Array as PropType<IProduct[]>
        }
    },
    emits: ['selectEngine'],
});
</script>