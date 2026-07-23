<template>
<SlotModal @closeModal="$emit('closeModal')">
    <div class="flex flex-col w-full gap-[22px] min-w-[750px] p-[16px]">
        <BaseInput v-for="item in [{ title: 'Название', name: 'name' }, { name: 'description', title: 'Описание' }]"
                   :props-class="'input-param'"
                   :props-label="item.title"
                   :props-value="item.name == 'name' ? parameter?.name : parameter?.description"
                   :props-placeholder="'...'"
                   @value-changed="(value) => changeValue(value, (item.name as 'name' | 'description'))" />
        <div class="flex flex-row justify-end gap-[15px]">
            <div v-for="item in ['Назад', 'Принять']">
                <BaseButton class="min-w-[200px]"
                            :propsClass="item == 'Назад' ? 'button-secondary' : 'button-primary'"
                            :disabled="item == 'Назад' ? false : disabled"
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
        return {
            newParameter,
            changeValue
        }
    }
});
</script>