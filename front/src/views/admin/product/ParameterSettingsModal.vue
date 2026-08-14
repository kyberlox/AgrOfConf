<template>
<SlotModal @closeModal="$emit('closeModal')">
    <div class="flex flex-col w-full gap-[22px] min-w-[750px] p-[16px]">
        <BaseInput v-for="(item, index) in [{ title: 'Название', name: 'name' }, { name: 'description', title: 'Описание' }]"
                   :inputSettings="initInputProps(item)"
                   :key="'navGroup' + index"
                   @value-changed="(value: string) => changeValue(value, (item.name as 'name' | 'description'))" />

        <div class="flex flex-row justify-end gap-[15px]">
            <div v-for="(item, index) in ['Назад', 'Принять']"
                 :key="'bread' + index">
                <BaseButton class="min-w-[200px]"
                            :buttonSettings="{ class: item == 'Назад' ? 'button-secondary' : 'button-primary', disabled: item == 'Назад' ? false : disabled }"
                            @click="item == 'Назад' ? $emit('closeModal') : $emit('updateParameter', parameter?.id, newParameter)">
                    <span>{{ item }}</span>
                </BaseButton>
            </div>
        </div>
    </div>
</SlotModal>
</template>

<script lang='ts'>
import SlotModal from '@/components/layout/SlotModal.vue';
import { defineComponent, type PropType, ref } from 'vue';
import type { IParameter } from '@/assets/interfaces/IParameter';
import { BaseButton, BaseInput } from 'beans-ui-kit';

export default defineComponent({
    components: {
        SlotModal,
        BaseInput,
        BaseButton
    },
    emits: ['closeModal', 'updateParameter'],
    props: {
        parameter: {
            type: Object as PropType<IParameter>
        },
        disabled: {
            type: Boolean
        }
    },
    setup(props) {
        const newParameter = ref({ name: '', description: '' });

        const changeValue = (value: string, key: keyof typeof newParameter.value) => {
            newParameter.value[key] = value;
        }

        const initInputProps = (item: { title: string, name: string }) => {
            return {
                class: 'input-param',
                label: item.title,
                value: item.name == 'name' ? props.parameter?.name : props.parameter?.description,
                placeholder: '...'
            }
        }

        return {
            newParameter,
            changeValue,
            initInputProps
        }
    }
});
</script>