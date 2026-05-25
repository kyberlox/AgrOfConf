<template>
<div class="flex flex-col items-center  min-h-screen gap-[16px]">
    <div class="text-(--icon-primary)">
        <Clip />
    </div>
    <h2 class="text-(--text-primary)">Опросных листов пока нет</h2>
    <div class="max-w-[340px] text-center text-(--text-secondary)">
        Создайте первый ОЛ, чтобы сформировать техническое
        коммерческое предложение
    </div>
    <BaseButton :props-class="'button-primary'"
                @clicked="$emit('createOl')">
        <ClipPlus />Создать ОЛ
    </BaseButton>
</div>
</template>
<script lang='ts'>
import { defineComponent } from 'vue';
import Clip from '@/assets/icons/Clip.svg?component';
import { BaseButton } from 'beans-ui-kit';
import ClipPlus from '@/assets/icons/ClipPlus.svg?component';

export default defineComponent({
    components: {
        Clip,
        ClipPlus,
        BaseButton
    },
    props: {},
    setup() {

        return {
        }
    }
});
</script>