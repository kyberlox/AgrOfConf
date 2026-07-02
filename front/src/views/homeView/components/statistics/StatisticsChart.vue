<template>
<div class="max-w-full h-[258px] w-full px-[24px]">
    <Line :data="chartData"
          :options="chartOptions" />
</div>
</template>

<script lang='ts'>
import { defineComponent, ref } from 'vue';
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
    props: {},
    setup() {
        const monthes = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];
        ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip);

        const customTooltip = ref({ visible: false, x: 0, y: 0, title: '', items: [] as { label: string; value: number; color: string }[], opacity: 0 });

        const chartData = {
            labels: monthes,
            datasets: [
                {
                    label: 'Ряд 1',
                    data: [10, 0, 14, 20, 2, 2, 6, 7, 9, 23, 11, 9],
                    borderColor: '#F36E3C',
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 6,
                    backgroundColor: '#F36E3C',
                    pointHitRadius: 100,
                    pointBorderColor: '#FFFFFF',
                    pointBorderWidth: 2,
                },
            ],
        }
        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
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