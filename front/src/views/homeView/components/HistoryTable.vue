<template>
<div class="w-full overflow-x-auto">
    <!-- Заглушка если нет истории -->
    <div v-if="!tableData.length || !isLogin"
         class="2xl:mt-[100px] xl:mt-[20px] ">
        <EmptyHistoryPlug @createOl="$emit('createOl')" />
    </div>
    <div v-else
         class="min-w-max">
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
            <tbody v-else>
                <tr class="bg-white hover:bg-gray-50 h-14 border-b border-gray-200 transition-colors"
                    v-for="(tr, index) in tableData"
                    :key="index + 'tableData'">
                    <td v-for="(td, index) in tr"
                        class="px-4 py-3 text-left text-sm font-medium text-gray-900 whitespace-nowrap first:pl-[48px]">
                        <div class="flex items-center">
                            <span class="truncate inline-block max-w-[200px]"
                                  :class="Number(index) == 0 ? 'underline cursor-pointer hover:text-orange-500 transition-colors duration-300' : ''">
                                {{ String(td).includes(':') ? td.split(' ')[0] : td }}
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
import EmptyHistoryPlug from '@/components/EmptyHistoryPlug.vue';
import { useUserStore } from '@/stores/user.ts';

export default defineComponent({
    components: { ArrowDown, EmptyHistoryPlug },
    emits: ['createOl'],
    props: {
        currentTableNav: {
            type: String as PropType<'requests' | 'statistics'>,
            required: true
        },
        tableData: {
            type: Array as PropType<string[][]>,
            required: true
        },
        tableHead: {
            type: Array as PropType<string[]>,
            required: true
        }
    },
    setup(props) {
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
            isLogin: computed(() => useUserStore().getIsLogin),
            numericPlugs: computed(() => props.currentTableNav == 'statistics' ? ['Старый оскол', 60, 21, 450, 50, 5650, 5643150, 564314150] : undefined),
        }
    }
})
</script>