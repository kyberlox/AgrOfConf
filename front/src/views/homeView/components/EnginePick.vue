<template>
<div class="p-[80px] flex flex-col gap-[16px] w-[calc(100vw-348px)]">
    <div class="flex flex-row items-center justify-between gap-[20px]">
        <h1 class="max-w-[160px]">
            Выберите изделие
        </h1>
        <div
             class="p-[20px] w-[480px] max-w-full border border-(--color-information-orange-200) hover:bg-(--color-information-orange-200) transition-all duration-300 cursor-pointer border-dotted flex flex-col gap-[4px] rounded-[12px] text-center">
            <span class="text-[16px] font-semibold text-(--color-information-orange-800)">Распознать ОЛ</span>
            <span class="text-[13px] font-normal text-(--text-text-secondary)">Фото или PDF до 20мб</span>
            <input class="hidden"
                   ref=fileInput
                   type="file"
                   @change="console.log('d')" />
        </div>
    </div>
    <!-- Карточки приводов -->
    <div class="flex flex-col gap-[12px]">
        <div class="flex flex-row gap-[16px]">
            <RouterLink v-for="item in items"
                        :to="{ name: 'configurator', params: { id: item.id } }"
                        :key="'engine' + item.id"
                        class="w-[200px] h-[274] p-[17px] cursor-pointer flex flex-col gap-[10px] border border-[#EAECEF] rounded-[8px] hover:border-orange-500 duration-300 transition-all"
                        @click="$emit('selectEngine', item.id)">
                <div class="bg-cover w-full h-[170px]"
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

export default defineComponent({
    components: {},
    props: {
        items: {
            type: Array as PropType<IProduct[]>
        }
    },
    setup() {
        return {}
    }
});
</script>