<template>
<div class="min-w-[250px] p-[24px] flex flex-col gap-[24px]">
    <h3>Выберите вариант ТКП</h3>
    <BaseSelect :propsId="'tkpVariants'"
                :props-placeholder="'Выберите варианты ТКП'"
                :propsClass="'paramsSelect'"
                :propsOptions="formatToSelect(tkpVariants)"
                @valueChanged="(id) => chosenVariant = id" />

    <BaseButton :propsClass="'button-primary'"
                @clicked=handleDownload>
        Скачать
    </BaseButton>
</div>
</template>
<script lang='ts'>
import { defineComponent, type PropType, ref } from 'vue';
import { type ITkpVariant } from '@/assets/interfaces/ITkpVariant.ts';
import { BaseSelect, BaseButton } from 'beans-ui-kit';

export default defineComponent({
    emits: ['downloadTkp'],
    components: {
        BaseSelect,
        BaseButton
    },
    props: {
        tkpVariants: {
            type: Array as PropType<ITkpVariant[]>,
            required: true
        }
    },
    setup(_, { emit }) {
        const chosenVariant = ref();

        const formatToSelect = (variants: ITkpVariant[]) => {
            return variants.map((variant) => {
                return {
                    label: variant.name,
                    value: variant.id
                }
            })
        }

        const handleDownload = () => {
            if (chosenVariant.value)
                emit('downloadTkp', chosenVariant)
        }

        return {
            chosenVariant,
            formatToSelect,
            handleDownload
        }
    }
}
);
</script>