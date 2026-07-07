<template>
<div class="w-full grow">
    <div v-if="section"
         class="text-(--orange) text-[16px] font-semibold">
        {{ section }}
    </div>

    <!-- Кнопки навигации и поиск-->
    <div class="min-h-screen mt-[32px] flex flex-col gap-[24px] bg-[#FDFDFD] border  border-[#EAECEF] rounded-[16px]">
        <div class="flex flex-row mt-[32px] gap-[24px] justify-between px-[24px] flex-wrap">
            <div class="flex flex-row gap-[24px] border-b-[1px] border-b-[#EAECEF] flex-grow flex-wrap">
                <div v-for="item in tableNav"
                     class="flex flex-row  items-center relative cursor-pointer px-[24px] hover:text-(--text-primary) duration-300"
                     :class="currentTableNav == item.name ? 'text-(--text-primary)' : 'text-(--text-secondary)'"
                     :key="item.id + 'tableNav'"
                     @click="handlePageTypeChange(item.name)">
                    <!-- Иконка -->
                    <Component :is="item.icon"
                               class="w-[24px] h-[24px] mr-[8px]">
                    </Component>
                    <!-- Название -->
                    <div>
                        {{ item.title }}
                    </div>
                    <span v-if="currentTableNav == item.name"
                          class="tableNav"></span>
                </div>
            </div>

            <!-- Поиск -->
            <BaseInput :propsClass="'searchInput'"
                       :propsPlaceholder="'Поиск'"
                       :type="'search'">
                <template #input-icon>
                    <SearchIcon />
                </template>
            </BaseInput>
        </div>

        <!-- Создать запрос -->
        <div v-if="tableData.length && !(currentTableNav == 'statistics')"
             class="flex items-center justify-end w-full px-[24px]">
            <BaseButton :props-class="'button-primary'"
                        @clicked="showEngineModal = true">
                <Blank class="w-[24px] h-[24px]" />
                <span>Создать ОЛ</span>
            </BaseButton>
        </div>

        <!-- Статистика пользователя -->
        <Statistics v-if="currentTableNav == 'statistics'" />

        <!--  Таблица запросов-->
        <HistoryTable :currentTableNav="currentTableNav"
                      :tableData="tableData"
                      :tableHead="Object.keys(headerComparsion)"
                      @create-ol="showEngineModal = true" />

        <!-- Модалка для выбора изделия -->
        <SlotModal v-if="showEngineModal"
                   @closeModal="showEngineModal = false">
            <EnginePick :items="engines" />
        </SlotModal>

    </div>
</div>
</template>
<script lang='ts'>
import { defineComponent, onMounted, ref, computed, watch } from 'vue';
import { tableNav } from '@/assets/static/tableNav';
import { BaseButton, BaseInput } from 'beans-ui-kit';
import SearchIcon from '@/assets/icons/SearchIcon.svg?component';
import Blank from '@/assets/icons/Blank.svg?component';
import EmptyHistoryPlug from '@/components/EmptyHistoryPlug.vue';
import SlotModal from '@/components/layout/SlotModal.vue';
import Api from '@/utils/Api';
import EnginePick from '@/views/homeView/components/EnginePickModal.vue'
import Configurator from '../configurator/Configurator.vue';
import { useProductsData } from '@/stores/products';
import { useNavStore } from '@/stores/navigation.ts';
import HistoryTable from './components/HistoryTable.vue';
import Statistics from './components/statistics/Statistics.vue';
import { useUserStore } from '@/stores/user.ts';
import { useHistoryStore } from '@/stores/historyTable.ts';
import { headerComparsion, formatResultToHistory } from '@/utils/historyTable.ts';
import { type IHistory } from '@/assets/interfaces/IHistory.ts';

export default defineComponent({
    components: {
        BaseInput,
        BaseButton,
        Blank,
        SearchIcon,
        EmptyHistoryPlug,
        SlotModal,
        EnginePick,
        Configurator,
        HistoryTable,
        Statistics
    },
    setup(props) {
        const showEngineModal = ref(false);
        const engines = ref([]);
        const engineId = ref<number>();
        const section = ref('Тест');
        const currentTableNav = computed(() => useNavStore().getCurrentNav);
        const navStore = useNavStore();
        const tableData = computed(() => useHistoryStore().getHistoryData);
        const userId = computed(() => useUserStore().getId);

        onMounted(async () => {
            try {
                const data = await Api.get('products/?skip=0&limit=100')
                useProductsData().setProducts(data);
                engines.value = data;
            } catch (error) {
                console.error('Error fetching products:', error);
            }
        })

        watch(() => userId.value, async () => {
            if (userId.value && !tableData.value.length)
                try {
                    const historyData: IHistory[] = await Api.get(`selection_statistic/selection?user_id=${userId.value}`)
                    useHistoryStore().setHistoryData(formatResultToHistory(historyData))
                } catch (error) {
                    console.error('Error history:', error)
                }
        }, { immediate: true })

        const handlePageTypeChange = (newType: "requests" | "statistics") => {
            navStore.setCurrentNav(newType)
        }

        return {
            engineId,
            tableNav,
            showEngineModal,
            engines,
            section,
            currentTableNav,
            tableData,
            headerComparsion,
            handlePageTypeChange,

        }
    }
});
</script>