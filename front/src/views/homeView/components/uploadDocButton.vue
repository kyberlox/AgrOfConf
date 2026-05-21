<template>
<div class="p-[20px] w-[480px] max-w-full border border-(--color-information-orange-200) hover:bg-(--color-information-orange-200) transition-all duration-300 cursor-pointer border-dotted flex flex-col gap-[4px] rounded-[12px] text-center"
     @click="handleClick">
    <span class="text-[16px] font-semibold text-(--color-information-orange-800)">
        Распознать ОЛ
    </span>
    <span class="text-[13px] font-normal text-(--text-text-secondary)">
        Фото или PDF до 20мб
    </span>
    <input class="hidden"
           ref=fileInput
           type="file"
           @change="console.log('d')" />
</div>
</template>
<script lang='ts'>
import { defineComponent, ref } from 'vue';

export default defineComponent({
    components: {},
    props: {},
    setup() {
        const fileInput = ref();
        const handleClick = () => {
            if (fileInput.value)
                (fileInput.value).click()
        }
        return {
            fileInput,
            handleClick
        }
    }
});
</script>