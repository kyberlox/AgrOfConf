<template>
<div class="w-full overflow-x-auto">
    <div class="min-w-max">
        <table class="w-full">
            <thead>
                <tr class="bg-[#F6F7F9] h-[56px]">
                    <th class="text-left text-sm font-medium first:pl-[48px] last:pr-[24px] not-first:not-last:p-[5px] whitespace-nowrap"
                        v-for="item in tableHead"
                        :key="item">
                        <div class="flex items-center">
                            <span class="truncate inline-block">
                                {{ item }}
                            </span>
                            <ArrowDown class="flex-shrink-0 ml-[9px]" />
                        </div>
                    </th>
                </tr>
            </thead>
            <tbody v-if="numericPlugs">
                <tr class="bg-white h-[56px]">
                    <td class="px-[48px] text-left text-sm font-medium whitespace-nowrap"
                        v-for="(item, index) in numericPlugs"
                        :key="item">
                        <div class="flex items-center">
                            <span class="truncate inline-block"
                                  :class="index == 0 ? 'underline cursor-pointer hover:text-[var(--orange)] duration-300 transition' : ''">
                                {{ item }}
                            </span>
                        </div>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</div>
</template>

<script lang="ts">
import { defineComponent, type PropType, computed, watch, ref } from 'vue';
import ArrowDown from '@/assets/icons/ArrowDown.svg?component';
import { useRoute } from 'vue-router';

export default defineComponent({
    components: { ArrowDown },
    props: {
        currentTableNav: {
            type: String as PropType<'requests' | 'statistics'>,
            required: true
        }
    },
    setup(props) {
        const tableHeadRequests = ref(['Шифр ОЛ', 'ОЛ №', 'Статус', 'Документ №', 'Готовность', 'Наименование', 'Шт.', 'Комментарий', 'Созд.', 'Готов']);
        const tableHeadStatistics = ref(['КО', 'ОЛ за мес.', 'ОЛ за год', 'ОЛ за все время', 'Запросов за мес.', 'Запросов за тек. мес.', 'Запросов за год', 'Запросов за все время'])
        const route = useRoute();

        watch(() => route.query, () => {
            if ('ko' in route.query && !('user' in route.query)) {
                tableHeadStatistics.value[0] = 'Пользователь'
            } else if ((!('ko' in route.query) && ('user' in route.query))) {
                tableHeadStatistics.value[0] = 'КО'
            }
            else {
                tableHeadStatistics.value[0] = '1'
            }
        }, { immediate: true, deep: true })

        return {
            tableHead: computed(() => props.currentTableNav == 'requests' ? tableHeadRequests.value : tableHeadStatistics.value),
            numericPlugs: computed(() => props.currentTableNav == 'statistics' ? ['Старый оскол', 60, 21, 450, 50, 5650, 5643150, 564314150] : []),
        }
    }
})
</script>