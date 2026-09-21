<template>
<SlotModal v-if="tkpModalIsVisible">
    <div class="min-w-[250px] p-[24px] flex flex-col gap-[12px]">
        <h3>Выберите вариант ТКП</h3>
        <div v-if="tkpVariants.length"
             class="flex flex-col gap-[6px]">
            <BaseSelect :selectSettings="initSelectProps(tkpVariants)"
                        @valueChanged="(id: string) => chosenVariant = id" />

            <BaseButton :button-settings="{ class: 'button-primary', disabled: tkpLoading }"
                        @clicked=handleDownload>
                <span v-if="!tkpLoading">Скачать</span>
                <Loader v-else />
            </BaseButton>
        </div>
        <span v-else>Ткп пока не загружены</span>
    </div>
</SlotModal>
</template>
<script lang='ts'>
import { defineComponent, type PropType, ref } from 'vue';
import { type ITkpVariant } from '@/assets/interfaces/ITkpVariant.ts';
import { BaseSelect, BaseButton } from 'beans-ui-kit';
import SlotModal from '@/components/layout/SlotModal.vue';
import Loader from '@/components/layout/Loader.vue';

export default defineComponent({
    emits: ['downloadTkp'],
    components: {
        BaseSelect,
        BaseButton,
        SlotModal,
        Loader
    },
    props: {
        tkpVariants: {
            type: Array as PropType<ITkpVariant[]>,
            required: true
        },
        tkpModalIsVisible: {
            type: Boolean,
            default: false
        },
        tkpLoading: {
            type: Boolean,
            default: false
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
                emit('downloadTkp', chosenVariant.value)
        }

        const initSelectProps = (tkpVariants: ITkpVariant[]) => {
            return {
                id: 'tkpVariants',
                placeholder: '...',
                class: 'select-primary',
                options: formatToSelect(tkpVariants)
            }
        }

        return {
            chosenVariant,
            initSelectProps,
            formatToSelect,
            handleDownload
        }
    }
}
);
</script>