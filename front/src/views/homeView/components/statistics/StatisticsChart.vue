<template>
<div class="max-w-full h-[258px] w-full px-[24px]"
     v-if="Object.keys(chartData).length">
    <Line :data="chartData"
          :options="chartOptions" />
    <div v-if="customTooltip.visible"
         class="absolute pointer-events-none z-50"
         :style="{ left: customTooltip.x + 'px', top: customTooltip.y + 'px', opacity: customTooltip.opacity }">
        <div
             class="bg-white  py-[16px] px-[24px] text-[12px] rounded-[16px] font-[700] shadow-[0_0_8px_0_rgba(180,188,200,0.5)]">
            <div>{{ customTooltip.title }}</div>
            <div v-for="(item) in customTooltip.items"
                 class="flex flex-row justify-between items-center text-[12px]">
                <span class="w-[6px] h-[6px] rounded-full"
                      :style="{ backgroundColor: item.color }"></span>
                {{ item.value }}
            </div>
        </div>
    </div>
</div>
</template>

<script lang='ts'>
import { defineComponent, ref, onMounted, computed, type PropType } from 'vue';
import { Line } from 'vue-chartjs';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Tooltip,
    type TooltipModel,
    type Chart,
    type TooltipItem
} from 'chart.js';

export default defineComponent({
    components: {
        Line
    },
    props: {
        monthes: {
            type: Array<string>,
            required: true
        },
        yearsDataset: {
            type: Object as PropType<{ current: Array<number>, previous: Array<number> }>,
            required: true
        }
    },
    setup(props) {
        ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip);

        const customTooltip = ref({ visible: false, x: 0, y: 0, title: '', items: [] as { label: string; value: number; color: string }[], opacity: 0 });

        const chartData = {
            labels: props.monthes,
            Tooltip: true,
            datasets: [
                {
                    label: 'За текущий год',
                    data: props.yearsDataset?.current,
                    borderColor: '#F36E3C',
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 6,
                    backgroundColor: '#F36E3C',
                    pointHitRadius: 100,
                    pointBorderColor: '#FFFFFF',
                    pointBorderWidth: 2,
                },
                {
                    label: 'За прошлый год',
                    data: props.yearsDataset?.previous,
                    borderColor: '#8E99A8',
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 6,
                    backgroundColor: '#8E99A8',
                    pointHitRadius: 100,
                    pointBorderColor: '#FFFFFF',
                    pointBorderWidth: 2,
                },
            ],
        }

        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index' as const,
                intersect: false,
            },
            plugins: {
                tooltip: {
                    enabled: false,
                    external: (context: { chart: Chart<'line'>; tooltip: TooltipModel<'line'> }) => {
                        const { chart, tooltip } = context

                        if (tooltip.opacity === 0) {
                            customTooltip.value.visible = false
                            customTooltip.value.opacity = 0
                            return
                        }

                        const position = chart.canvas.getBoundingClientRect()
                        customTooltip.value.visible = true
                        customTooltip.value.x = position.left + tooltip.caretX
                        customTooltip.value.y = position.top + tooltip.caretY
                        customTooltip.value.title = tooltip.title?.[0] || ''
                        customTooltip.value.items = tooltip.dataPoints.map((point: TooltipItem<'line'>) => ({
                            label: point.dataset.label ?? '',
                            value: point.parsed.y ?? 0,
                            color: (point.dataset.backgroundColor as string) ?? '#000'
                        }))
                        customTooltip.value.opacity = 1
                    }
                }
            }
        }
        return {
            chartData,
            chartOptions,
            customTooltip
        }
    }
});
</script>