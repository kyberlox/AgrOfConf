<template>
<div class="flex flex-col items-center gap-[16px]">
    <div class="text-(--icon-primary)">
        <Clip />
    </div>
    <h2 class="text-(--text-primary)">
        {{ isLogin && !isSearchResult ?
            `Опросных листов пока нет` : isSearchResult ? 'По вашему запросу нет совпадений' :
                `Вы неавторизованы` }}
    </h2>
    <div class="max-w-[340px] text-center text-(--text-secondary)">
        {{
            isLogin ?
                'Создайте первый ОЛ, чтобы сформировать техническое коммерческое предложение' :
                `Войдите в систему, чтобы пользоваться историей и статистикой`
        }}
    </div>
    <BaseButton :props-class="'button-primary'"
                @clicked="$emit('createOl')">
        <ClipPlus />
        Создать ОЛ
    </BaseButton>
</div>
</template>
<script lang='ts'>
import { defineComponent, computed } from 'vue';
import Clip from '@/assets/icons/Clip.svg?component';
import { BaseButton } from 'beans-ui-kit';
import ClipPlus from '@/assets/icons/ClipPlus.svg?component';
import { useUserStore } from '@/stores/user.ts';

export default defineComponent({
    components: {
        Clip,
        ClipPlus,
        BaseButton
    },
    props: {
        isSearchResult: {
            type: Boolean,
            required: true
        }
    },
    setup() {
        return {
            isLogin: computed(() => useUserStore().getIsLogin)
        }
    }
});
</script>