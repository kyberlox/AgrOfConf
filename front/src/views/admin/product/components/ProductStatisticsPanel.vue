<template>
    <section class="mt-[20px] border border-gray-200 p-[20px] rounded-xl">
        <h3 class="text-lg font-medium mb-2">Статистика подборов по продукту</h3>
        <p v-if="!statistics.length" class="text-sm text-gray-500">Пока нет данных о подборах.</p>
        <ul v-else class="flex flex-col gap-2 max-h-[220px] overflow-auto">
            <li
                v-for="(statistic, index) in statistics"
                :key="`${statistic.document_number}-${statistic.date_search}-${index}`"
                class="text-sm flex flex-row justify-between gap-4 border-b border-gray-100 pb-1">
                <span>Документ №{{ statistic.document_number ?? "-" }}</span>
                <span>{{ statistic.date_search ?? "" }} — {{ statistic.status ?? "" }}</span>
            </li>
        </ul>
    </section>
</template>

<script lang="ts">
import { defineComponent, type PropType } from "vue";
import type { ProductStatistic } from "../types";

export default defineComponent({
    props: {
        statistics: {
            type: Array as PropType<ProductStatistic[]>,
            required: true,
        },
    },
});
</script>
