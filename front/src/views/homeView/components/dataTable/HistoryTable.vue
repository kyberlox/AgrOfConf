<template>
    <div v-if="currentTableNav !== 'statistics' && tableHead" class="w-full h-[700px]">
        <!-- Заглушка если нет истории -->
        <div v-if="!tableData.length && tableReady" class="2xl:mt-[100px] xl:mt-[20px]">
            <EmptyHistoryPlug
                :isEmptyPage="total > 1 && Number(activePage) > total"
                :isSearchResult="isSearchResult"
                @navToFirstPage="navToPage(1)"
                @createOl="$emit('createOl')" />
        </div>
        <div v-else-if="tableData.length && tableReady" class="w-full relative h-full flex flex-col">
            <AgGridVue
                class="w-full h-full grow"
                :rowData="rowData"
                :columnDefs="columnDefs"
                :defaultColDef="defaultColDef"
                :theme="theme"
                :rowHeight="56"
                :headerHeight="56"
                :domLayout="'autoHeight'"
                :reactiveCustomComponents="true"
                :autoSizeStrategy="autoSizeStrategy"
                :tooltipShowMode="'whenTruncated'"
                :tooltipShowDelay="10"
                @cell-clicked="(x: ICellClicked) => handleCellClicked(x)"
                @grid-ready="onGridReady"
                @grid-size-changed="autoSize" />
            <Pagination
                v-if="total && rowsPerPage"
                :rowsPerPage="rowsPerPage"
                :total="totalPages"
                :activePage="String(activePage)"
                @toPage="(page: number) => navToPage(page)" />
        </div>
        <div v-else class="engine-params__loader">
            <Loader />
        </div>
    </div>
</template>

<script lang="ts">
import { defineComponent, type PropType, computed, shallowRef, ref, watch } from "vue";
import { AgGridVue } from "ag-grid-vue3";
import EmptyHistoryPlug from "@/components/EmptyHistoryPlug.vue";
import CellRenderer from "./CellRenderer.vue";
import { useUserStore } from "@/stores/user.ts";
import { historyTableTheme } from "@/assets/static/historyThemeAdGrid.ts";
import Pagination from "./TablePagination.vue";
import Loader from "@/components/layout/Loader.vue";
import TextTooltip from "@/components/layout/TextTooltip.vue";
import { useRoute, useRouter } from "vue-router";
import { type ICellClicked, type IHistoryResponse } from "@/assets/interfaces/IHistory.ts";
import { headerComparsionOl, headerComparsionReq } from "@/utils/historyTable.ts";

import {
    ModuleRegistry,
    type ColDef,
    type GridApi,
    type GridReadyEvent,
    type AutoSizeStrategy,
    ClientSideRowModelModule,
    ColumnAutoSizeModule,
    ValidationModule,
    themeAlpine,
    CellStyleModule,
    TooltipModule,
} from "ag-grid-community";

ModuleRegistry.registerModules([
    ClientSideRowModelModule,
    ColumnAutoSizeModule,
    ValidationModule,
    CellStyleModule,
    TooltipModule,
]);
const theme = themeAlpine.withParams(historyTableTheme);

export default defineComponent({
    name: "HistoryTable",
    components: {
        AgGridVue,
        EmptyHistoryPlug,
        CellRenderer,
        Pagination,
        Loader,
        TextTooltip,
    },
    emits: ["createOl", "pageChanged"],
    props: {
        currentTableNav: {
            type: String as PropType<"requests" | "statistics">,
            required: true,
        },
        tableData: {
            type: Array as PropType<string[][]>,
            required: true,
        },
        tableReady: {
            type: Boolean,
            default: false,
        },
        isSearchResult: {
            type: Boolean,
            default: false,
        },
        total: {
            type: Number,
            required: true,
        },
        rowsPerPage: {
            type: Number,
            default: 10,
        },
        historyData: {
            type: Object as PropType<IHistoryResponse>,
            required: true,
        },
    },
    setup(props, { emit }) {
        const gridApi = shallowRef<GridApi | null>(null);
        const route = useRoute();
        const router = useRouter();
        const activePage = computed(() => route.query.page || 1);
        const totalPages = computed(() => Math.ceil(props.total / props.rowsPerPage));
        const requestId = computed(() => route.query.requestId);
        const tableHead = ref<string[]>([]);
        watch(
            () => requestId.value,
            () => {
                tableHead.value = Object.keys(requestId.value ? headerComparsionOl : headerComparsionReq);
            },
            { immediate: true },
        );

        const columnMinWidths: Record<string, number> = {
            Наименование: 250,
            "Шифр ОЛ": 200,
            "Запрос №": 150,
        };
        const columnMaxWidths: Record<string, number> = {
            "Шт.": 100,
        };

        const rowData = computed(() => {
            return props.tableData.map((row) => {
                const obj: Record<string, string | number> = {};
                tableHead.value.forEach((header, index) => {
                    const raw = row[index];
                    if (raw === undefined || raw === null) {
                        obj[header] = "Не определено";
                    } else if (/^\d+$/.test(raw)) {
                        obj[header] = raw;
                    } else {
                        obj[header] = raw;
                    }
                });
                return obj;
            });
        });

        const defaultColDef: ColDef = {
            sortable: true,
            resizable: false,
            autoHeight: false,
            wrapText: false,
            cellClass: "ag-custom-cell",
            headerClass: "ag-custom-header",
        };

        const autoSizeStrategy: AutoSizeStrategy = {
            type: "fitGridWidth",
        };

        const columnDefs = computed<ColDef[]>(() => {
            return tableHead.value.map((header, index) => ({
                field: header,
                headerName: header,
                cellRenderer: "CellRenderer",
                cellRendererParams: {
                    colDefs: tableHead,
                },
                tooltipValueGetter: (params) => params.value,
                tooltipComponent: "TextTooltip",
                sortable: true,
                minWidth: columnMinWidths[header],
                maxWidth: columnMaxWidths[header],
            }));
        });

        const autoSize = () => {
            gridApi.value?.sizeColumnsToFit();
        };

        const onGridReady = (params: GridReadyEvent) => {
            gridApi.value = params.api;
        };

        const onFirstDataRendered = () => {
            autoSize();
        };

        const navToPage = (page: number) => {
            router.push({ query: { page: page < 1 ? 1 : page > totalPages.value ? totalPages.value : page } });
            emit("pageChanged", page);
        };

        const handleCellClicked = (rowData: ICellClicked) => {
            if (rowData.column.colId !== "Шифр ОЛ" && rowData.column.colId !== "Запрос №") return;
            const targetRow = props.historyData.data?.find((e) => e.id == rowData.value);
            router.push(
                rowData.column.colId == "Шифр ОЛ"
                    ? {
                          name: "configurator",
                          params: { id: String(targetRow?.product_id) },
                          query: { code: String(targetRow?.id), requestId: String(requestId.value) },
                      }
                    : {
                          name: "myRequest",
                          query: { requestId: String(rowData.value) },
                      },
            );
        };

        return {
            rowData,
            columnDefs,
            defaultColDef,
            autoSizeStrategy,
            theme,
            gridApi,
            totalPages,
            activePage,
            tableHead,
            autoSize,
            onGridReady,
            onFirstDataRendered,
            navToPage,
            handleCellClicked,
            isLogin: computed(() => useUserStore().getIsLogin),
        };
    },
});
</script>
<style>
.ag-root-wrapper {
    border: none;
    border-radius: 0;
}

.ag-grid-pinned-top-rows {
    z-index: 0;
}

.ag-header {
    border-bottom: none;
}

.ag-header-row {
    border-bottom: none;
}

.ag-cell {
    display: flex;
    align-items: center;
    border: none;
    outline: none;
}

.ag-cell:first-child,
.ag-header-cell:first-child {
    padding-left: 24px;
}

.ag-cell:focus {
    border: none;
    outline: none;
}

.ag-row {
    transition: background-color 0.2s;
}

.ag-row:last-child {
    border-bottom: none;
}

.ag-cell-focus,
.ag-cell:focus-visible {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}

.ag-sort-order {
    display: none;
}

.ag-root {
    border: none;
}
</style>
