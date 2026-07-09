<template>
<div v-if="currentTableNav !== 'statistics'"
     class="w-full">
    <!-- Заглушка если нет истории -->
    <div v-if="(!rowData.length)"
         class="2xl:mt-[100px] xl:mt-[20px]">
        <EmptyHistoryPlug @createOl="$emit('createOl')" />
    </div>
    <div v-else
         class="w-full">
        <AgGridVue :rowData="rowData"
                   :columnDefs="columnDefs"
                   :defaultColDef="defaultColDef"
                   :theme="theme"
                   :rowHeight="56"
                   :headerHeight="56"
                   :domLayout="'autoHeight'"
                   :reactiveCustomComponents="true"
                   :autoSizeStrategy="autoSizeStrategy"
                   @grid-ready="onGridReady"
                   class="w-full" />
    </div>
</div>
</template>
<script lang="ts">
import { defineComponent, type PropType, computed, shallowRef, watch } from 'vue';
import { AgGridVue } from 'ag-grid-vue3';
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
    CellStyleModule
} from 'ag-grid-community';
import EmptyHistoryPlug from '@/components/EmptyHistoryPlug.vue';
import CellRenderer from './CellRenderer.vue';
import { useUserStore } from '@/stores/user.ts';
import { historyTableTheme } from '@/assets/static/historyThemeAdGrid.ts';
import { useLayoutStore } from '@/stores/layout.ts';

ModuleRegistry.registerModules([
    ClientSideRowModelModule,
    ColumnAutoSizeModule,
    ValidationModule,
    CellStyleModule
]);
const theme = themeAlpine
    .withParams(historyTableTheme);

export default defineComponent({
    name: 'HistoryTable',
    components: { AgGridVue, EmptyHistoryPlug, CellRenderer },
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
        const gridApi = shallowRef<GridApi | null>(null);
        const isSidebarRolled = computed(() => useLayoutStore().isSidebarRolled);

        const columnMinWidths: Record<string, number> = {
            'Наименование': 250,
            'Шифр ОЛ': 200,
        };
        const columnMaxWidths: Record<string, number> = {
            'Шт.': 100,
        };

        const rowData = computed(() => {
            return props.tableData.map(row => {
                const obj: Record<string, string | number> = {};
                props.tableHead.forEach((header, index) => {
                    const raw = row[index];
                    if (raw === undefined || raw === null) {
                        obj[header] = 'Не определено';
                    } else if (/^\d+$/.test(raw)) {
                        obj[header] = (raw);
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
            cellClass: 'ag-custom-cell',
            headerClass: 'ag-custom-header',
        };

        const autoSizeStrategy: AutoSizeStrategy = {
            type: 'fitGridWidth',
        };

        const columnDefs = computed<ColDef[]>(() => {
            return props.tableHead.map((header, index) => ({
                field: header,
                headerName: header,
                cellRenderer: 'CellRenderer',
                cellRendererParams: {
                    colDefs: props.tableHead
                },
                sortable: true,
                minWidth: columnMinWidths[header],
                maxWidth: columnMaxWidths[header],
            }));
        });

        const autoSize = () => {
            gridApi.value?.sizeColumnsToFit();
        }

        const onGridReady = (params: GridReadyEvent) => {
            gridApi.value = params.api;
        };

        const onFirstDataRendered = () => {
            autoSize()
        }

        watch((isSidebarRolled), () => {
            autoSize()
        })

        return {
            rowData,
            columnDefs,
            defaultColDef,
            autoSizeStrategy,
            theme,
            autoSize,
            onGridReady,
            onFirstDataRendered,
            isLogin: computed(() => useUserStore().getIsLogin),
        }
    }
})
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