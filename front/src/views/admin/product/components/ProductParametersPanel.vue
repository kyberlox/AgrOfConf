<template>
    <section class="flex flex-col gap-[20px]">
        <div
            v-if="!parameters.length"
            class="mt-4 border border-dashed border-gray-300 p-[24px] rounded-xl text-center text-gray-500">
            <p class="text-[16px] font-medium mb-1">Параметры продукта ещё не заданы</p>
            <p class="text-sm">
                Загрузите Excel‑таблицу в блоке «Excel» — будут созданы таблица и её параметры, либо создайте параметр
                вручную кнопкой «Создать параметр».
            </p>
        </div>

        <div v-else class="flex flex-col gap-2 mt-4 border border-gray-200 p-[20px] rounded-xl">
            <div class="flex flex-row justify-start gap-[40px] flex-wrap">
                <div v-for="item in parameterLegend" :key="item.label" class="flex flex-row gap-[15px]">
                    <h3>{{ item.label }}</h3>
                    <div class="w-[20px] h-[20px] rounded-md" :class="item.color"></div>
                </div>
            </div>

            <VueDraggable
                v-model="parameters"
                :animation="150"
                target=".sort-target"
                @start="handleSortStart"
                @end="handleSortEnd">
                <TransitionGroup
                    type="transition"
                    tag="ul"
                    :name="dragging ? undefined : 'fade'"
                    class="sort-target grid grid-cols-1 lg:grid-cols-4 gap-4 max-w-full mt-4">
                    <ProductParameterCard
                        v-for="parameter in parameters"
                        :key="parameter.id"
                        :parameter="parameter"
                        @delete="$emit('deleteParameter', $event)"
                        @edit="$emit('editParameter', $event)" />
                </TransitionGroup>
            </VueDraggable>
        </div>
    </section>
</template>

<script lang="ts">
import { computed, defineComponent, nextTick, ref, TransitionGroup, type PropType } from "vue";
import { VueDraggable } from "vue-draggable-plus";
import type { IParameter } from "@/assets/interfaces/IParameter";
import ProductParameterCard from "./ProductParameterCard.vue";

const parameterLegend = [
    { label: "Табличные параметры", color: "bg-green-200" },
    { label: "Формульные параметры", color: "bg-blue-200" },
] as const;

export default defineComponent({
    components: {
        ProductParameterCard,
        TransitionGroup,
        VueDraggable,
    },
    props: {
        modelValue: {
            type: Array as PropType<IParameter[]>,
            required: true,
        },
    },
    emits: ["update:modelValue", "sortStart", "sortEnd", "deleteParameter", "editParameter"],
    setup(props, { emit }) {
        const dragging = ref(false);
        const parameters = computed({
            get: () => props.modelValue,
            set: (value) => emit("update:modelValue", value),
        });

        const handleSortStart = () => {
            dragging.value = true;
            emit("sortStart");
        };

        const handleSortEnd = () => {
            nextTick(() => {
                dragging.value = false;
                emit("sortEnd");
            });
        };

        return {
            dragging,
            parameters,
            parameterLegend,
            handleSortStart,
            handleSortEnd,
        };
    },
});
</script>

<style>
.fade-move,
.fade-enter-active,
.fade-leave-active {
    transition: all 0.5s cubic-bezier(0.55, 0, 0.1, 1);
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
    transform: scaleY(0.01) translate(30px, 0);
}

.fade-leave-active {
    position: absolute;
}
</style>
