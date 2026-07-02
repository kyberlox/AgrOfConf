<template>
<div class="mt-[24px] px-[24px] flex-wrap">
    <section class="flex flex-row gap-[32px] ">
        <StatisticsBlocks :statBlocks="statBlocks"
                          :type="'ol'" />
        <StatisticsPie />
        <StatisticsBlocks :statBlocks="statBlocks"
                          :type="'requests'" />

    </section>

    <section class="mt-[24px] py-[24px] rounded-[16px] border border-[#D3D7DF]">
        <StatisticsChart />
    </section>
</div>
</template>

<script lang='ts'>
import StatisticsChart from './StatisticsChart.vue';
import { defineComponent, ref, computed, watch, markRaw } from 'vue';
import ThunderIcon from '@/assets/icons/Thunder.svg?component';
import TimeIcon from '@/assets/icons/Time.svg?component';
import CalendarIcon from '@/assets/icons/Calendar.svg?component';
import PulseIcon from '@/assets/icons/Pulse.svg?component';
import type { IStatisticBlock, IStatisticResponse } from '@/assets/interfaces/IStatistic.ts';
import { useUserStore } from '@/stores/user.ts';
import Api from '@/utils/Api.ts';
import StatisticsBlocks from './StatisticsBlocks.vue';
import StatisticsPie from './StatisticsPie.vue';

export default defineComponent({
    components: {
        StatisticsChart,
        StatisticsBlocks,
        StatisticsPie,
        ThunderIcon,
        TimeIcon,
        CalendarIcon,
        PulseIcon,

    },
    props: {},
    setup() {
        const userId = computed(() => useUserStore().getId);
        const statBlocks = ref<IStatisticBlock[]>([
            { name: 'month', title: 'за тек. месяц', value: null, icon: markRaw(ThunderIcon), undertext: 'к предыдущему месяцу', comparsion: null },
            { name: 'day', title: 'за день', value: null, icon: markRaw(TimeIcon), undertext: 'к предыдущему дню', comparsion: null },
            { name: 'year', title: 'за год', value: null, icon: markRaw(PulseIcon), undertext: 'к предыдущему году', comparsion: null },
            { name: 'total', title: 'за все время', value: null, icon: markRaw(CalendarIcon), undertext: 'с начала работы', comparsion: null }
        ]);

        watch(() => userId.value, async () => {
            if (!userId.value) return;
            try {
                const res: IStatisticResponse = await Api.get(`selection_statistic/metrics?user_id=${userId.value}`)
                Object.keys(res).forEach(key => {
                    const target = statBlocks.value.find(block => block.name === key);
                    if (!target) return
                    const val = res[key as keyof IStatisticResponse];
                    target.value = typeof val == 'object' && 'current' in val ? val.current : val || 0;
                    target.comparsion = typeof val == 'object' && 'diff' in val ? val.diff : val || 0;
                })
            } catch (error) {
                console.error('Error fetching statistics:', error);
            }
        }, { immediate: true })

        return {
            statBlocks,
        }
    }
});
</script>