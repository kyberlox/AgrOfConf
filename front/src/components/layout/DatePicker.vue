<template>
    <VueDatePicker
        v-model="date"
        :enable-time-picker="false"
        auto-apply
        :week-start="1"
        ref="datePickerRef"
        :formats="{ input: format }"
        :hide-offset-dates="true"
        :time-picker="false"
        :locale="ru"
        @update-month-year="(value: { month: number; year: number }) => updateMonth(value)">
        <template #menu-header>
            <div class="my-header border-0! flex flex-row justify-between py-[16px]! text-[14px]">
                <div
                    @click="datePickerRef.switchView('month')"
                    class="flex flex-row items-center gap-[8px] font-semibold">
                    {{ activeMonth }}
                    <DawDawn />
                </div>
                <span @click="datePickerRef.switchView('year')">
                    {{ currentYear }}
                </span>
            </div>
        </template>
        <template #day="{ day, date }">
            <template v-if="checkDay(date) == 'вс' || checkDay(date) == 'сб'">
                <div class="text-red-500!">{{ day }}</div>
            </template>
            <template v-else class="text-red">
                {{ day }}
            </template>
        </template>
        <template #action-extra="">
            <div class="flex flex-row justify-start items-center py-[16px]">
                <span v-if="activeMonth !== 'Декабрь'" class="text-[14px]" @click="goToNextMonth">
                    {{ nextMonth }}
                </span>
            </div>
        </template>
    </VueDatePicker>
</template>
<script lang="ts">
import { defineComponent, ref, computed, watch } from "vue";
import { VueDatePicker } from "@vuepic/vue-datepicker";
import "@vuepic/vue-datepicker/dist/main.css";
import { ru } from "date-fns/locale";
import DawDawn from "@/assets/icons/DawDown.svg?component";
import { upFirstLetter } from "@/utils/stringUtil";
import { format } from "@/utils/dateUtil";

export default defineComponent({
    components: {
        VueDatePicker,
        DawDawn,
    },
    props: {},
    emits: ["newDate"],
    setup(_, { emit }) {
        const datePickerRef = ref();
        const currentMonth = ref(new Date().getMonth());
        const currentYear = ref(new Date().getFullYear());
        const date = ref(new Date());

        const goToNextMonth = () => {
            const nextMonth = currentMonth.value++;
            datePickerRef.value.setMonthYear({ month: nextMonth, year: currentYear.value + 1 });
            currentMonth.value++;
        };

        const updateMonth = (value: { month: number }) => {
            currentMonth.value = value.month + 1;
        };

        watch(
            () => date.value,
            () => {
                emit("newDate", date.value);
            },
            { immediate: true },
        );

        return {
            date,
            currentMonth,
            activeMonth: computed(() =>
                upFirstLetter(
                    new Date(new Date().setMonth(currentMonth.value)).toLocaleString("ru", { month: "long" }),
                ),
            ),
            nextMonth: computed(() =>
                upFirstLetter(
                    new Date(new Date().setMonth(currentMonth.value + 1)).toLocaleString("ru", { month: "long" }),
                ),
            ),
            currentYear,
            datePickerRef,
            ru,
            format,
            updateMonth,
            goToNextMonth,
            checkDay: (date: Date) => date.toLocaleString("ru", { weekday: "short" }),
        };
    },
});
</script>

<style>
.my-header {
    padding: 5px;
    border: 1px solid red;
    width: 100%;
    text-align: center;
}
.dp--month-year-wrap {
    /* display: none; */
}
.dp--month-year-wrap .dp--arrow-top,
.dp--month-year-wrap .dp--month-year-header,
.dp--month-year-wrap .dp--calendar-header {
    display: none;
}
.dp--menu-inner {
    padding: 0;
}
.dp--month-year-wrap .dp--arrow-top {
    display: none;
}
.dp--tp-wrap {
    display: none;
}
.dp--calendar-header-separator {
    display: none;
}
.dp--menu {
    padding-inline: 16px;
}
.dp--cell-offset {
    visibility: hidden;
}
.dp--arrow-top {
    display: none;
}

.dp--calendar-header {
    display: none;
}

.dp--btn-base.dp--bg-none.dp--month-year-select-base.dp--month-year-select {
    display: none;
}
.dp--btn-base.dp--bg-none.dp--arrow-btn-nav {
    display: none;
}
</style>
