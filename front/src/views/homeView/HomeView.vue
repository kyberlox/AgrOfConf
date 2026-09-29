<template>
    <div class="w-full grow">
        <!-- <div v-if="section"
         class="text-(--orange) text-[16px] font-semibold">
        {{ section }}
    </div> -->

        <!-- Кнопки навигации и поиск-->
        <div class="min-h-[86vh] flex flex-col gap-[24px] bg-[#FDFDFD] border border-[#EAECEF] rounded-[16px]">
            <div class="flex flex-row mt-[32px] gap-[24px] justify-between px-[24px] flex-wrap">
                <div class="flex flex-row gap-[24px] border-b-[1px] border-b-[#EAECEF] flex-grow flex-wrap">
                    <div
                        v-for="item in tableNav"
                        class="flex flex-row items-center relative cursor-pointer px-[24px] hover:text-(--text-primary) duration-300 pb-[10px]"
                        :class="currentTableNav == item.name ? 'text-(--text-primary)' : 'text-(--text-secondary)'"
                        :key="item.id + 'tableNav'"
                        @click="handlePageTypeChange(item.name)">
                        <!-- Иконка -->
                        <Component :is="item.icon" class="w-[24px] h-[24px] mr-[8px]"> </Component>
                        <!-- Название -->
                        <div>
                            {{ item.title }}
                        </div>
                        <span v-if="currentTableNav == item.name" class="tableNav"></span>
                    </div>
                </div>

                <!-- Поиск -->
                <BaseInput
                    v-if="userId"
                    :propsClass="'input-search'"
                    :propsPlaceholder="'Поиск'"
                    :type="'search'"
                    :inputSettings="{ class: 'input-search', placeholder: 'Поиск', type: 'search' }"
                    @value-changed="search">
                    <template #input-icon>
                        <SearchIcon />
                    </template>
                </BaseInput>
            </div>

            <!-- Создать запрос -->
            <div class="flex flex-row justify-between px-[24px] items-center">
                <!-- <RequestCard
                    v-if="requestId"
                    :requestId="requestId"
                    :requestInfo="historyData?.data.find((e) => e.id == requestId)" /> -->
                <div v-if="tableData?.length && !(currentTableNav == 'statistics')" class="flex justify-end w-full">
                    <BaseButton :buttonSettings="{ class: 'button-primary' }" @clicked="handleCreateClick">
                        <Blank class="w-[24px] h-[24px]" />
                        <span>{{ requestId ? "Создать ОЛ" : "Создать запрос" }}</span>
                    </BaseButton>
                </div>
            </div>

            <!-- Статистика пользователя -->
            <Statistics v-if="currentTableNav == 'statistics'" />

            <!--  Таблица запросов-->
            <HistoryTable
                v-if="historyData"
                :currentTableNav="currentTableNav"
                :tableReady="tableReady"
                :tableData="tableData || []"
                :isSearchResult="!!textToSearch"
                :rowsPerPage="rowsPerPage"
                :total="totalHistoryRows"
                :requestId="requestId"
                :historyData="historyData"
                @pageChanged="(page: number) => changePage(page)"
                @createOl="showEngineModal = true" />

            <!-- Модалка для выбора изделия -->
            <EnginePickModal
                v-if="requestId"
                :items="engines"
                :requestId="String(requestId)"
                :showEngineModal="showEngineModal"
                @closeModal="showEngineModal = false" />

            <CreateRequestModal
                v-if="createRequestVisible"
                @closeModal="createRequestVisible = false"
                @goToReq="goToReq" />
        </div>
    </div>
</template>
<script lang="ts">
import { defineComponent, onMounted, ref, computed, watch } from "vue";
import { tableNav } from "@/assets/static/tableNav";
import { BaseButton, BaseInput } from "beans-ui-kit";
import SearchIcon from "@/assets/icons/SearchIcon.svg?component";
import Blank from "@/assets/icons/Blank.svg?component";
import SlotModal from "@/components/layout/SlotModal.vue";
import Api from "@/utils/Api";
import EnginePickModal from "@/views/homeView/components/EnginePickModal.vue";
import Configurator from "../configurator/Configurator.vue";
import { useProductsData } from "@/stores/products";
import { useNavStore } from "@/stores/navigation.ts";
import HistoryTable from "./components/dataTable/HistoryTable.vue";
import Statistics from "./components/statistics/Statistics.vue";
import { useUserStore } from "@/stores/user.ts";
import { useHistoryStore } from "@/stores/historyTable.ts";
import { formatResultToHistory } from "@/utils/historyTable.ts";
import { type IHistoryResponse } from "@/assets/interfaces/IHistory.ts";
import { useRoute, useRouter } from "vue-router";
import CreateRequestModal from "@/views/homeView/components/createRequestModal/CreateRequestModal.vue";
import RequestCard from "./components/RequestCard.vue";

export default defineComponent({
    components: {
        BaseInput,
        BaseButton,
        Blank,
        SearchIcon,
        SlotModal,
        EnginePickModal,
        Configurator,
        HistoryTable,
        Statistics,
        CreateRequestModal,
        RequestCard,
    },
    setup(props) {
        const showEngineModal = ref(false);
        const engines = ref([]);
        const engineId = ref<number>();
        const section = ref("Тест");
        const currentTableNav = computed(() => useNavStore().getCurrentNav);
        const navStore = useNavStore();
        const tableData = computed(() => useHistoryStore().getHistoryData);
        const userId = computed(() => useUserStore().getId);
        const tableReady = ref(false);
        const textToSearch = ref("");
        const totalHistoryRows = ref<number>(0);
        const rowsPerPage = ref(10);
        const currentPage = ref(Number(useRoute().query.page || 1));
        const historyData = ref<IHistoryResponse>();
        const createRequestVisible = ref(false);
        const router = useRouter();
        const route = useRoute();
        const requestId = computed(() => route.query?.requestId || null);

        const getHistoryData = async () => {
            const getSkip = () => {
                return currentPage.value < 1 ? 0 : (currentPage.value - 1) * rowsPerPage.value;
            };
            const checkRoute = () => {
                if (requestId.value) {
                    return `selection_statistic/selection?user_id=${userId.value}&skip=${getSkip()}&request_id=${requestId.value}`;
                } else return "requests/user?skip=0&limit=100";
            };

            try {
                tableReady.value = false;
                historyData.value = (await Api.get(checkRoute())) as IHistoryResponse;
                useHistoryStore().setHistoryData(
                    formatResultToHistory(historyData.value, requestId.value ? "ol" : "req"),
                );
                totalHistoryRows.value = Number(historyData.value.total_count);
            } finally {
                tableReady.value = true;
            }
        };

        onMounted(async () => {
            textToSearch.value = "";
            const data = await Api.get("products/?skip=0&limit=100");
            if (!data) return;
            useProductsData().setProducts(data);
            engines.value = data;
        });

        watch(
            [() => userId.value, () => requestId.value],
            async () => {
                if (!userId.value) return;
                getHistoryData();
            },
            { immediate: true },
        );

        const handlePageTypeChange = (newType: "requests" | "statistics") => {
            navStore.setCurrentNav(newType);
        };

        let abortController: AbortController | null = null;
        const search = async (newTextToSearch: string, page: number = 1) => {
            if (!newTextToSearch && newTextToSearch !== "") return;
            textToSearch.value = newTextToSearch;
            if (abortController) {
                abortController.abort();
            }
            abortController = new AbortController();
            try {
                if (!newTextToSearch) {
                    return getHistoryData();
                }
                const searchRes = await Api.get(
                    `/selection_statistic/search_by_value?value=${textToSearch.value}&skip=${rowsPerPage.value}`,
                    abortController,
                );
                if (!searchRes.result) return;
                useHistoryStore().setHistoryData(formatResultToHistory(searchRes, requestId.value ? "ol" : "req"));
            } catch (e) {
                console.error(e);
            }
        };

        const changePage = (page: number) => {
            currentPage.value = page;
            getHistoryData();
        };

        const goToReq = (chosenRequestId: number) => {
            router.push({ name: "myRequest", query: { requestId: chosenRequestId } });
        };

        const handleCreateClick = () => {
            if (!requestId.value) {
                createRequestVisible.value = true;
            } else showEngineModal.value = true;
        };

        return {
            engineId,
            tableNav,
            showEngineModal,
            engines,
            section,
            currentTableNav,
            tableData,
            tableReady,
            textToSearch,
            userId,
            totalHistoryRows,
            rowsPerPage,
            historyData,
            createRequestVisible,
            requestId,
            handleCreateClick,
            handlePageTypeChange,
            search,
            changePage,
            goToReq,
        };
    },
});
</script>
