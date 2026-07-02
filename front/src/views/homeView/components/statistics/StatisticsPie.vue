<template>
<div class="flex flex-col gap-[16px] w-full max-w-[246px] ">
    <div class="flex flex-row gap-[16px]">
        <div class="min-w-fit text-[16px] font-[700] leading-[120%] text-(--text-text-primary)">Статус ОЛ за тек. мес.
        </div>
        <div class="divider"></div>
    </div>

    <div
         class="w-full h-full rounded-[16px] border border-(--color-information-orange-200) bg-[linear-gradient(140deg,#fff_0%,#fff2e5_100%)] flex flex-col gap-[16px] items-start justify-start overflow-hidden p-[24px]">
        <div class="px-[8px]">
            <span class="text-[14px] text-(--text-text-primary) font-[700] leading-[120%] block">
                Новых ОЛ:
                <span class="text-[16px] font-[900]">14</span>
            </span>
            <span class="text-[11px] text-(--text-text-secondary) font-[500] leading-[120%]">
                основано на новых запросах
            </span>
        </div>
        <div class="relative self-center">
            <Doughnut :data="chartData"
                      :width="142"
                      :height="142"
                      :options="chartOptions" />
            <div
                 class="absolute transform -translate-x-1/2 -translate-y-1/2 top-1/2 left-1/2 flex flex-col text-center">
                <div class="text-[36px] font-black text-center leading-[100%]">63</div>
                <div class="text-[11px] text-(--text-text-secondary) leading-[120%]">% в статусе</div>
                <div class="text-[11px] font-[700] text-(--text-text-primary) leading-[120%]">открыт</div>
            </div>
        </div>
        <div class="flex flex-col gap-[8px] w-full">
            <div v-for="(row, index) in statuses"
                 :key="'row' + index"
                 class="flex flex-row items-center justify-between w-full">
                <div class="flex flex-row gap-[4px] items-center w-fit rounded-[16px] pl-[8px] py-[4px] min-w-[50%] items-center"
                     :class="`bg-(--color-information-${row.color}-50)`">
                    <span class="rounded-[100%] w-[5px] h-[5px]"
                          :class="`bg-(--color-information-${row.color}-400)`"></span>
                    <span class="font-[500] text-[11px] leading-[120%]">
                        {{ row.name }}
                    </span>
                </div>
                <div>{{ row.value }}%</div>
            </div>
        </div>
    </div>
</div>
</template>

<script lang='ts'>
import { defineComponent } from 'vue';
import { Doughnut } from 'vue-chartjs';
import {
    Chart as ChartJS,
    ArcElement,
    Tooltip,
    Legend
} from 'chart.js';

export default defineComponent({
    components: {
        Doughnut
    },
    props: {},
    setup() {
        ChartJS.register(ArcElement, Tooltip, Legend);

        const statuses = [
            {
                name: 'Открыт',
                value: 63,
                color: 'orange'
            },
            {
                name: 'Завершен',
                value: 32,
                color: 'green'
            },
            {
                name: 'Отклонен',
                value: 5,
                color: 'red'
            },
        ]

        const chartData = {
            labels: ['Открыт', 'завершен', 'Отклонен'],
            datasets: [
                {
                    label: 'Статистика',
                    data: statuses.map(e => e.value),
                    backgroundColor: ['#FFCBA5', '#A5D6A7', '#F49494'],
                    borderColor: ['#FFFFFF', '#FFFFFF', '#FFFFFF'],
                    borderWidth: 2,
                    hoverOffset: 8
                },
            ],
        };

        const chartOptions = {
            responsive: false,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                }
            },
        };



        return {
            chartData,
            chartOptions,
            statuses
        };
    }
});
</script>