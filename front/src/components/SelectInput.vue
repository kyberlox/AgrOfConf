<template>
<div v-for="(item, index) in inputsCount"
     class="flex flex-col gap-[24px] col-span-full w-full">
    <div class="flex flex-row justify-between w-full gap-[8px]">
        <BaseSelect :propsClass="'paramsSelect'"
                    :props-options="param.all_values"
                    :props-label="'Компонент'"
                    :props-placeholder="'Выберите компонент'"
                    :error="'error' in param && choices.find(e => e.name && e.value) && index == 0 ? param.error : ''"
                    @value-changed="(x) => handleValueChange(x, index, 'select')">
            <AlertCircle />
        </BaseSelect>

        <BaseInput :propsClass="'input-select'"
                   :props-type="'number'"
                   :props-placeholder="'в %'"
                   :propsName="param.name + (index + 1)"
                   :props-label="'Мольная доля, %'"
                   :min="Number(0)"
                   :max="Number(100)"
                   :error="'error' in param ? param.error : ''"
                   @valueChanged="(x) => handleValueChange(x, index, 'input')" />
    </div>
    <div v-if="index !== item - 1"
         class="border border-[#EAECEF] w-full h-[1px] col-span-full m-auto"></div>
</div>
</template>

<script lang='ts'>
import { defineComponent, type PropType, ref, watch } from 'vue';
import { BaseInput, BaseSelect } from 'beans-ui-kit';
import type { IFormattedData } from '@/assets/interfaces/IForm';
import AlertCircle from '@/assets/icons/AlertCircle.svg?component';

export default defineComponent({
    components: {
        BaseSelect,
        BaseInput,
        AlertCircle
    },
    props: {
        param: {
            type: Object as PropType<IFormattedData>,
            required: true
        }
    },
    emits: ['changeSelectInputValue'],
    setup(props, { emit }) {
        const choices = ref<{ name: string, value: number }[]>([]);
        const inputsCount = ref(1);

        const handleValueChange = (value: string | number, index: number, type: 'select' | 'input') => {
            if (!choices.value[index]) {
                choices.value.push({ name: '', value: 0 })
            }

            switch (type == 'select') {
                case true:
                    choices.value[index]!.name = String(value || 0);
                    break;
                case false:
                    choices.value[index]!.value = Number(value || 0);
                    break;
                default:
                    break;
            }

            const sum = choices.value.reduce((acc, cur) => acc + cur.value, 0);
            if (sum < 100) {
                if (!choices.value.some(e => !e.value)) inputsCount.value = choices.value.length + 1;
            } else {
                inputsCount.value = choices.value.filter(e => e.value).length;
            }
            emit('changeSelectInputValue', choices.value.filter(e => e.name && e.value).map(e => ({
                [e.name]: e.value
            })))
        }

        return {
            inputsCount,
            choices,
            handleValueChange
        }
    }
});
</script>