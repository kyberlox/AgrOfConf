<template>
<div class="w-full ag-theme-custom"
     v-if="currentTableNav !== 'statistics'">
    <!-- Заглушка если нет истории -->
    <div v-if="(!rowData.length || !isLogin)"
         class="2xl:mt-[100px] xl:mt-[20px]">
        <EmptyHistoryPlug @createOl="$emit('createOl')" />
    </div>
    <div v-else
         class="min-w-max">
        <AgGridVue :rowData="rowData"
                   :columnDefs="columnDefs"
                   :defaultColDef="defaultColDef"
                   :modules="modules"
                   :domLayout="'autoHeight'"
                   :suppressMovableColumns="true"
                   :enableCellTextSelection="true"
                   :ensureDomOrder="true"
                   :animateRows="false"
                   :rowHeight="56"
                   :headerHeight="56"
                   :suppressBrowserResizeObserver="false"
                   :stopEditingWhenCellsLoseFocus="true"
                   :reactiveCustomComponents="true"
                   @first-data-rendered="onFirstDataRendered"
                   class="ag-theme-custom w-full" />
    </div>
</div>
</template>

<script lang="ts">
import { defineComponent, type PropType, computed, ref } from 'vue';
import { AgGridVue } from 'ag-grid-vue3';
import { ModuleRegistry, type ColDef, type GridReadyEvent } from 'ag-grid-community';
import { AllCommunityModule } from 'ag-grid-community';
import EmptyHistoryPlug from '@/components/EmptyHistoryPlug.vue';
import CellRenderer from './CellRenderer.vue';
import { useUserStore } from '@/stores/user.ts';

// Регистрация модулей AG Grid (обязательно для v36+)
ModuleRegistry.registerModules([AllCommunityModule]);

// Импорт стилей
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';

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
        const gridApi = ref<any>(null);
        const modules = [AllCommunityModule];

        const rowData = computed(() => {
            return props.tableData.map(row => {
                const obj: Record<string, string | number> = {};
                props.tableHead.forEach((header, index) => {
                    const raw = row[index];
                    if (raw === undefined || raw === null) {
                        obj[header] = 'Не определено';
                    } else if (/^\d+$/.test(raw)) {
                        obj[header] = Number(raw);
                    } else {
                        obj[header] = raw;
                    }
                });
                return obj;
            });
        });

        const defaultColDef: ColDef = {
            sortable: true,
            resizable: true,
            suppressMovable: true,
            autoHeight: false,
            wrapText: false,
            suppressAutoSize: false,
            cellClass: 'ag-custom-cell',
            headerClass: 'ag-custom-header',
        };

        const columnDefs = computed<ColDef[]>(() => {
            return props.tableHead.map((header) => ({
                field: header,
                headerName: header,
                cellRenderer: 'CellRenderer',
                cellRendererParams: {
                    colDefs: props.tableHead
                },
                minWidth: 10,
                maxWidth: 148,
                width: undefined,
                flex: undefined,
                sortable: true,
                filter: false,
                comparator: (valueA: any, valueB: any) => {
                    if (typeof valueA === 'number' && typeof valueB === 'number') {
                        return valueA - valueB;
                    }
                    const strA = String(valueA ?? '');
                    const strB = String(valueB ?? '');
                    return strA.localeCompare(strB, 'ru');
                }
            }));
        });

        const onFirstDataRendered = (params: GridReadyEvent) => {
            gridApi.value = params.api;
            setTimeout(() => {
                params.api.autoSizeAllColumns();
            }, 50);
        };

        return {
            rowData,
            columnDefs,
            defaultColDef,
            modules,
            onFirstDataRendered,
            isLogin: computed(() => useUserStore().getIsLogin),
        }
    }
})
</script>

<style>
/* ===== AG Grid Custom Theme ===== */
.ag-theme-custom {
    --ag-border-color: #EAECEF;
    --ag-row-border-color: #E5E7EB;
    --ag-header-background-color: #F6F7F9;
    --ag-header-foreground-color: #111827;
    --ag-background-color: #FFFFFF;
    --ag-odd-row-background-color: #FFFFFF;
    --ag-row-hover-color: #F9FAFB;
    --ag-font-family: inherit;
    --ag-font-size: 14px;
    --ag-cell-horizontal-padding: 16px;
    --ag-cell-horizontal-margin: 0;
    --ag-borders: none;
    --ag-row-border-width: 1px;
    --ag-row-border-style: solid;
    --ag-header-column-separator-display: none;
    --ag-header-column-resize-handle-display: block;
    --ag-header-column-resize-handle-width: 1px;
    --ag-header-column-resize-handle-height: 30%;
    --ag-header-column-resize-handle-color: #D1D5DB;
    --ag-selected-row-background-color: transparent;
    --ag-range-selection-border-color: transparent;
    --ag-range-selection-background-color: transparent;
    --ag-cell-widget-spacing: 0px;
}

/* Сброс лишних обводок AG Grid */
.ag-theme-custom .ag-root-wrapper {
    border: none;
    border-radius: 0;
}

.ag-theme-custom .ag-header {
    border-bottom: none;
    font-weight: 500;
    background-color: #F6F7F9 !important;
}

.ag-theme-custom .ag-header-row {
    border-bottom: none;
    background-color: #F6F7F9 !important;
}

.ag-theme-custom .ag-header-cell {
    background-color: #F6F7F9 !important;
}

/* Ячейки */
.ag-theme-custom .ag-cell {
    display: flex;
    align-items: center;
    font-weight: 500;
    color: #111827;
    line-height: 1.25rem;
    border: none;
    outline: none;
}

.ag-theme-custom .ag-cell:focus {
    border: none;
    outline: none;
}

/* Hover строки */
.ag-theme-custom .ag-row {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E5E7EB;
    transition: background-color 0.2s;
}

.ag-theme-custom .ag-row:hover {
    background-color: #F9FAFB;
}

.ag-theme-custom .ag-row:last-child {
    border-bottom: none;
}

/* Убираем фокусные рамки */
.ag-theme-custom .ag-cell-focus,
.ag-theme-custom .ag-cell:focus-visible {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}

/* Скрываем сортировочные стрелки AG Grid */
.ag-theme-custom .ag-sort-order {
    display: none;
}

/* Убираем зазор под таблицей при autoHeight */
.ag-theme-custom.ag-theme-alpine {
    --ag-grid-size: 0px;
}

.ag-theme-custom .ag-root {
    border: none;
}
</style>