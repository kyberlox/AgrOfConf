<template>
<div class="border border-gray-200 p-[20px] rounded-xl">
    <div class="flex flex-row flex-wrap items-center justify-between gap-[12px] mb-[12px]">
        <h3 class="text-lg font-medium">Блоки параметров</h3>
        <div class="flex flex-row gap-[8px] flex-wrap">
            <BaseButton :buttonSettings="{ class: 'button-secondary' }"
                        @clicked="createBlock">
                Создать блок
            </BaseButton>
            <BaseButton :buttonSettings="{ class: 'button-primary' }"
                        @clicked="generateContacts">
                Сгенерировать «Контактные данные»
            </BaseButton>
        </div>
    </div>

    <p class="text-sm text-gray-500 mb-[12px]">
        Перетащите параметры в нужный блок (или обратно в «Не распределены»).
        Порядок блоков меняется стрелками. Свойства блока (редактируемость, видимость)
        применяются ко всем его параметрам.
    </p>

    <Loader v-if="loading" />

    <div v-else-if="!blocks.length && !unassigned.length"
         class="border border-dashed border-gray-300 p-[16px] rounded-xl text-center text-gray-500 text-sm">
        Пока нет ни блоков, ни параметров. Создайте блок или сгенерируйте «Контактные данные».
    </div>

    <div v-else class="flex flex-col gap-[12px]">
        <!-- Пул нераспределённых параметров -->
        <div class="border border-dashed border-gray-300 rounded-xl p-[12px]"
             @dragover.prevent
             @drop.prevent="dropOnUnassigned">
            <div class="text-sm font-medium text-gray-700 mb-[8px]">
                Не распределены <span class="text-gray-400">({{ unassigned.length }})</span>
            </div>
            <div class="flex flex-row flex-wrap gap-[8px]">
                <span v-for="p in unassigned"
                      :key="p.id"
                      draggable="true"
                      class="param-chip"
                      :class="{ 'opacity-40': isDragging(p) }"
                      @dragstart="dragStart(p, null)"
                      @dragend="dragEnd">
                    {{ p.name }}
                </span>
                <span v-if="!unassigned.length" class="text-xs text-gray-400">Перетащите сюда параметры, чтобы убрать их из блоков</span>
            </div>
        </div>

        <!-- Блоки -->
        <div v-for="(block, index) in blocks"
             :key="block.id"
             class="border border-blue-200 bg-blue-50/40 rounded-xl p-[12px]"
             @dragover.prevent
             @drop.prevent="dropOnBlock(block.id)">
            <div class="flex flex-row items-center justify-between gap-[8px] mb-[8px] flex-wrap">
                <div class="flex flex-row items-center gap-[8px] min-w-0 flex-wrap">
                    <span class="text-sm font-semibold text-gray-800 truncate">{{ block.name }}</span>
                    <span class="text-xs text-gray-400">({{ block.params.length }})</span>
                    <span v-if="block.properties?.editable === false"
                          class="text-[11px] px-[6px] py-[1px] rounded-full bg-orange-100 text-orange-700">только просмотр</span>
                    <span v-if="block.properties?.visibility === false"
                          class="text-[11px] px-[6px] py-[1px] rounded-full bg-gray-200 text-gray-600">скрыт</span>
                </div>
                <div class="flex flex-row items-center gap-[6px] shrink-0">
                    <button type="button" title="Вверх"
                            class="w-[24px] h-[24px] rounded-md bg-white border border-gray-200 text-gray-600 hover:bg-gray-100"
                            :disabled="index === 0"
                            @click="moveBlock(block, -1)">↑</button>
                    <button type="button" title="Вниз"
                            class="w-[24px] h-[24px] rounded-md bg-white border border-gray-200 text-gray-600 hover:bg-gray-100"
                            :disabled="index === blocks.length - 1"
                            @click="moveBlock(block, 1)">↓</button>
                    <button type="button" title="Изменить свойства блока"
                            class="w-[24px] h-[24px] rounded-md bg-white border border-gray-200 text-gray-600 hover:bg-gray-100"
                            @click="openEditBlock(block)">✎</button>
                    <button type="button" title="Удалить блок"
                            class="w-[24px] h-[24px] rounded-md bg-white border border-red-200 text-red-600 hover:bg-red-50"
                            @click="deleteBlock(block)">✕</button>
                </div>
            </div>
            <div class="flex flex-row flex-wrap gap-[8px] min-h-[40px]">
                <span v-for="p in block.params"
                      :key="p.id"
                      draggable="true"
                      class="param-chip param-chip--in-block"
                      :class="{ 'opacity-40': isDragging(p) }"
                      @dragstart="dragStart(p, block.id)"
                      @dragend="dragEnd">
                    {{ p.name }}
                </span>
                <span v-if="!block.params.length" class="text-xs text-gray-400">Перетащите сюда параметры</span>
            </div>
        </div>
    </div>

    <!-- Модалка редактирования блока -->
    <div v-if="editingBlock"
         class="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
        <div class="bg-white rounded-lg p-6 w-full max-w-md shadow-xl">
            <h1 class="text-lg font-medium mb-4">Свойства блока</h1>
            <div class="flex flex-col gap-3">
                <label class="flex flex-col gap-1 text-sm">
                    <span class="text-gray-700">Название</span>
                    <input class="input-param w-full" v-model="editingBlock.name" />
                </label>
                <label class="flex flex-col gap-1 text-sm">
                    <span class="text-gray-700">Описание</span>
                    <input class="input-param w-full" v-model="editingBlock.description" />
                </label>
                <label class="flex flex-row items-center gap-2 text-sm text-gray-700 cursor-pointer">
                    <input type="checkbox" v-model="editingBlock.editable" />
                    Доступен для выбора значений
                </label>
                <label class="flex flex-row items-center gap-2 text-sm text-gray-700 cursor-pointer">
                    <input type="checkbox" v-model="editingBlock.visibility" />
                    Видим пользователю
                </label>
                <label class="flex flex-col gap-1 text-sm">
                    <span class="text-gray-700">Отображение параметров блока</span>
                    <select class="input-param w-full" v-model="editingBlock.display">
                        <option value="group">Все сразу</option>
                        <option value="sequential">Друг за другом</option>
                    </select>
                </label>
            </div>
            <div class="flex justify-end gap-3 mt-5">
                <button class="px-4 py-2 rounded bg-gray-200 hover:bg-gray-300"
                        @click="editingBlock = null">
                    Назад
                </button>
                <button class="px-4 py-2 rounded text-white bg-orange-500 hover:bg-orange-600"
                        @click="saveBlock">
                    Сохранить
                </button>
            </div>
        </div>
    </div>
</div>
</template>

<script lang='ts'>
import Api from '@/utils/Api';
import { defineComponent, onMounted, ref, watch } from 'vue';
import { BaseButton } from 'beans-ui-kit';
import Loader from '@/components/layout/Loader.vue';

interface BlockParam {
    id: number;
    name: string;
    type?: string;
    required_type?: string;
}

interface ParamBlock {
    id: number;
    name: string;
    description?: string | null;
    sort: number;
    properties?: Record<string, any>;
    params: BlockParam[];
}

export default defineComponent({
    components: { BaseButton, Loader },
    props: {
        productId: {
            type: [String, Number] as unknown as undefined,
            default: null
        }
    },
    emits: ['changed'],
    setup(props, { emit }) {
        const blocks = ref<ParamBlock[]>([]);
        const unassigned = ref<BlockParam[]>([]);
        const loading = ref(false);
        const dragging = ref<{ param: BlockParam; blockId: number | null } | null>(null);
        const editingBlock = ref<{ id: number; name: string; description: string; editable: boolean; visibility: boolean; display: string } | null>(null);

        const safeProductId = () => {
            const id = Number(props.productId);
            return Number.isFinite(id) ? id : null;
        };

        const loadManage = async () => {
            const pid = safeProductId();
            if (!pid) {
                blocks.value = [];
                unassigned.value = [];
                return;
            }
            loading.value = true;
            try {
                const data = await Api.get(`blocks/manage/${pid}`);
                blocks.value = data?.blocks ?? [];
                unassigned.value = data?.unassigned ?? [];
            } catch (e) {
                console.error('blocks/manage', e);
            } finally {
                loading.value = false;
            }
        };

        const refreshAfter = async () => {
            await loadManage();
            emit('changed');
        };

        const createBlock = async () => {
            const pid = safeProductId();
            if (!pid) return;
            const name = window.prompt('Название нового блока');
            if (!name || !name.trim()) return;
            try {
                await Api.post('blocks/', { product_id: pid, name: name.trim() });
                await refreshAfter();
            } catch (e: any) {
                alert(e?.response?.data?.detail || 'Не удалось создать блок');
            }
        };

        const generateContacts = async () => {
            const pid = safeProductId();
            if (!pid) return;
            try {
                await Api.post(`blocks/${pid}/generate_contacts`);
                await refreshAfter();
            } catch (e) {
                console.error('generate_contacts', e);
            }
        };

        const openEditBlock = (block: ParamBlock) => {
            editingBlock.value = {
                id: block.id,
                name: block.name,
                description: block.description ?? '',
                editable: block.properties?.editable !== false,
                visibility: block.properties?.visibility !== false,
                display: block.properties?.display || 'group'
            };
        };

        const saveBlock = async () => {
            const b = editingBlock.value;
            if (!b) return;
            try {
                await Api.put(`blocks/${b.id}`, {
                    name: b.name,
                    description: b.description,
                    properties: { editable: b.editable, visibility: b.visibility, display: b.display }
                });
                editingBlock.value = null;
                await refreshAfter();
            } catch (e: any) {
                alert(e?.response?.data?.detail || 'Не удалось сохранить блок');
            }
        };

        const deleteBlock = async (block: ParamBlock) => {
            if (!window.confirm(`Удалить блок «${block.name}»? Его параметры станут не распределёнными.`)) return;
            try {
                await Api.delete(`blocks/${block.id}`);
                await refreshAfter();
            } catch (e) {
                console.error('delete block', e);
            }
        };

        const moveBlock = async (block: ParamBlock, dir: number) => {
            const idx = blocks.value.findIndex(b => b.id === block.id);
            const target = idx + dir;
            if (idx < 0 || target < 0 || target >= blocks.value.length) return;
            const arr = [...blocks.value];
            const [moved] = arr.splice(idx, 1);
            arr.splice(target, 0, moved);
            blocks.value = arr;
            const items = arr.map((b, i) => ({ id: b.id, sort: i + 1 }));
            try {
                await Api.post('blocks/reorder', { items });
            } catch (e) {
                console.error('reorder blocks', e);
                await loadManage();
            }
        };

        const dragStart = (param: BlockParam, blockId: number | null) => {
            dragging.value = { param, blockId };
        };
        const dragEnd = () => {
            dragging.value = null;
        };
        const isDragging = (param: BlockParam) => dragging.value?.param?.id === param.id;

        const removeFromSource = (param: BlockParam) => {
            for (const b of blocks.value) {
                const i = b.params.findIndex(p => p.id === param.id);
                if (i >= 0) { b.params.splice(i, 1); return; }
            }
            const i = unassigned.value.findIndex(p => p.id === param.id);
            if (i >= 0) unassigned.value.splice(i, 1);
        };

        const dropOnBlock = async (blockId: number) => {
            const d = dragging.value;
            if (!d) return;
            removeFromSource(d.param);
            const target = blocks.value.find(b => b.id === blockId);
            if (target) target.params.push(d.param);
            dragging.value = null;
            try {
                await Api.post(`blocks/${blockId}/assign`, { parameter_ids: [d.param.id] });
            } catch (e) {
                console.error('assign', e);
                await loadManage();
            }
        };

        const dropOnUnassigned = async () => {
            const d = dragging.value;
            if (!d) return;
            removeFromSource(d.param);
            unassigned.value.push(d.param);
            dragging.value = null;
            try {
                await Api.post('blocks/unassign', { parameter_ids: [d.param.id] });
            } catch (e) {
                console.error('unassign', e);
                await loadManage();
            }
        };

        onMounted(loadManage);
        watch(() => props.productId, loadManage);

        return {
            blocks,
            unassigned,
            loading,
            editingBlock,
            createBlock,
            generateContacts,
            openEditBlock,
            saveBlock,
            deleteBlock,
            moveBlock,
            dragStart,
            dragEnd,
            isDragging,
            dropOnBlock,
            dropOnUnassigned
        };
    }
});
</script>

<style scoped>
.param-chip {
    display: inline-flex;
    align-items: center;
    padding: 6px 12px;
    border-radius: 999px;
    font-size: 13px;
    background: #fff;
    border: 1px solid #d1d5db;
    color: #374151;
    cursor: grab;
    user-select: none;
}
.param-chip--in-block {
    background: #eff6ff;
    border-color: #bfdbfe;
}
</style>