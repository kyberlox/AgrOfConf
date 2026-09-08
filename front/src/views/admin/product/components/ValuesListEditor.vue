<template>
<div class="flex flex-col gap-[8px]">
    <label class="text-sm text-gray-700">Список значений (для «Выбора из списка»)</label>
    <div v-if="list.length"
         class="flex flex-col gap-[6px]">
        <div v-for="(val, index) in list"
             :key="index"
             class="flex flex-row items-center gap-[8px]">
            <input class="input-param w-full"
                   :value="val"
                   placeholder="Значение"
                   @input="updateValue(index, ($event.target as HTMLInputElement).value)" />
            <button class="text-red-500 hover:text-red-700 shrink-0 whitespace-nowrap"
                    title="Удалить значение"
                    @click="removeValue(index)">
                Удалить
            </button>
        </div>
    </div>
    <p v-else
       class="text-sm text-gray-400">
        Список пуст — значения будут храниться, но выбор из списка не будет показывать варианты.
    </p>
    <button class="w-fit text-sm text-blue-600 hover:text-blue-800"
            @click="addValue">
        + Добавить значение
    </button>
</div>
</template>

<script lang='ts'>
import { defineComponent, ref, watch } from 'vue';

export default defineComponent({
    name: 'ValuesListEditor',
    props: {
        values: {
            type: Array as () => string[],
            default: () => []
        }
    },
    emits: ['update:values'],
    setup(props, { emit }) {
        const list = ref<string[]>([...(props.values || [])]);

        watch(() => props.values, (v) => {
            list.value = [...(v || [])]
        })

        const addValue = () => {
            list.value.push('')
            emit('update:values', [...list.value])
        }

        const updateValue = (index: number, value: string) => {
            list.value[index] = value
            emit('update:values', [...list.value])
        }

        const removeValue = (index: number) => {
            list.value.splice(index, 1)
            emit('update:values', [...list.value])
        }

        return {
            list,
            addValue,
            updateValue,
            removeValue
        }
    }
});
</script>