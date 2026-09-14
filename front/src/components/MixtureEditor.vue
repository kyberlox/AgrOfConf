<template>
<div class="flex flex-col gap-[4px] w-full py-[6px] px-[4px]">
    <span class="text-[13px] text-[#343B4C] font-[600]">{{ param.name }}</span>
    <button type="button"
            class="flex flex-row items-center justify-between gap-[8px] w-full px-[10px] py-[8px] rounded-[8px] border border-[#EAECEF] bg-white hover:border-[#d4d4d4] hover:shadow-sm text-left"
            :disabled="disabled"
            @click="openEditor">
        <span v-if="currentLabel"
              class="text-[13px] text-[#343B4C]">{{ currentLabel }}</span>
        <span v-else
              class="text-[13px] text-[#8E99A8]">Составить смесь</span>
        <span class="text-[12px] text-[#F36E3C] whitespace-nowrap">Изменить</span>
    </button>
    <span v-if="'error' in param && param.error"
          class="text-[12px] text-red-500">{{ param.error }}</span>

    <teleport to="body">
        <div v-if="editorVisible"
             class="fixed inset-0 z-50 flex items-center justify-center bg-[#00000040]"
             @click.self="closeEditor">
            <div class="bg-white rounded-[12px] p-[20px] w-[min(90vw,620px)] max-h-[80vh] flex flex-col gap-[14px] shadow-xl">
                <div class="flex flex-row justify-between items-center">
                    <h2 class="text-[16px] font-[600] text-[#343B4C]">{{ param.name }}</h2>
                    <button type="button"
                            class="w-[26px] h-[26px] rounded-[100%] bg-[#F6F7F9] flex items-center justify-center cursor-pointer text-[#8E99A8] hover:text-[#343B4C]"
                            @click="closeEditor">✕</button>
                </div>

                <div class="text-[13px] text-[#8E99A8]">
                    Выберите рабочую среду и укажите её мольную долю. Обязательно две среды
                    и более; сумма долей должна составлять ровно 100%.
                </div>

                <div class="flex flex-col gap-[8px] max-h-[300px] overflow-y-auto">
                    <div v-for="(row, index) in rows"
                         :key="index"
                         class="flex flex-row items-center gap-[8px]">
                        <select class="input-param w-full"
                                :value="row.name"
                                :disabled="disabled"
                                @change="row.name = (($event.target as HTMLSelectElement).value)">
                            <option value="">— Среда —</option>
                            <option v-for="option in availableOptions(row, index)"
                                    :key="option"
                                    :value="option">{{ option }}</option>
                        </select>
                        <input class="input-param w-[110px]"
                               type="number"
                               min="0"
                               max="100"
                               step="any"
                               :disabled="disabled"
                               :value="row.share === null ? '' : row.share"
                               placeholder="доля, %"
                               @input="row.share = parseShare(($event.target as HTMLInputElement).value)" />
                        <button type="button"
                                class="w-[26px] h-[26px] shrink-0 rounded-[100%] bg-[#FFF2E5] text-[#F36E3C] flex items-center justify-center cursor-pointer hover:bg-[#FFE4CC]"
                                :disabled="rows.length <= 1"
                                @click="removeRow(index)">✕</button>
                    </div>
                </div>

                <button type="button"
                        class="self-start px-[12px] py-[6px] rounded-[8px] border border-dashed border-[#F36E3C] text-[13px] text-[#F36E3C] hover:bg-[#FFF2E5] disabled:opacity-50 disabled:cursor-not-allowed"
                        :disabled="!canAddRow || disabled"
                        @click="addRow">+ Добавить среду</button>

                <div class="flex flex-col gap-[8px] border-t border-[#EAECEF] pt-[12px]">
                    <div class="flex flex-row justify-between text-[13px]">
                        <span class="text-[#343B4C]">Сумма мольных долей</span>
                        <span :class="sum === 100 ? 'text-green-600 font-[600]' : 'text-[#F36E3C] font-[600]'">
                            {{ sum.toFixed(2) }}%
                        </span>
                    </div>
                    <div v-if="!isValid && rows.some(r => r.name)"
                         class="text-[12px] text-[#8E99A8]">
                        {{ mustTwoMedia ? 'Добавьте ещё одну среду — смесь должна состоять минимум из двух сред.' : sum < 100 ? `Добавьте сред ещё на ${(100 - sum).toFixed(2)}%` : `Сумма превышает 100% на ${(sum - 100).toFixed(2)}%` }}
                    </div>
                    <div class="flex flex-row justify-end gap-[10px] mt-[4px]">
                        <button type="button"
                                class="px-[16px] py-[8px] rounded-[8px] bg-gray-200 hover:bg-gray-300 text-[#343B4C]"
                                @click="closeEditor">Отмена</button>
                        <button type="button"
                                class="px-[16px] py-[8px] rounded-[8px] text-white bg-[#F36E3C] hover:bg-[#E05A2A] disabled:opacity-50 disabled:cursor-not-allowed"
                                :disabled="!isValid || disabled"
                                @click="applyComposition">Применить</button>
                    </div>
                </div>
            </div>
        </div>
    </teleport>
</div>
</template>

<script lang='ts'>
import { defineComponent, type PropType, ref, computed, watch } from 'vue';
import type { IFormattedData } from '@/assets/interfaces/IForm';

interface IMixtureRow {
    name: string;
    share: number | null;
}

export default defineComponent({
    props: {
        param: {
            type: Object as PropType<IFormattedData>,
            required: true,
        },
        disabled: {
            type: Boolean,
            default: false,
        },
        mediaOptions: {
            type: Array as PropType<string[]>,
            default: () => [],
        },
        modelValue: {
            type: Array as PropType<Array<{ [key: string]: number }>>,
            default: () => [],
        },
    },
    emits: ['valueChanged'],
    setup(props, { emit }) {
        const editorVisible = ref(false);
        const rows = ref<IMixtureRow[]>([]);

        const parseShare = (text: string): number | null => {
            if (!text.trim()) return null;
            const value = Number(text.replace(',', '.'));
            return Number.isFinite(value) ? value : null;
        }

        const fromComposition = (composition: Array<{ [key: string]: number }>): IMixtureRow[] => {
            const result: IMixtureRow[] = [];
            for (const item of composition) {
                for (const [name, share] of Object.entries(item)) {
                    result.push({ name, share: Number(share) || null });
                }
            }
            return result;
        }

        const currentComposition = computed<Array<{ [key: string]: number }>>(() => {
            if (Array.isArray(props.modelValue) && props.modelValue.length) {
                return props.modelValue;
            }
            const rv = props.param?.response_value;
            if (Array.isArray(rv)) return rv;
            return [];
        });

        const currentLabel = computed<string>(() => {
            if (!Array.isArray(currentComposition.value) || !currentComposition.value.length) return '';
            return currentComposition.value
                .flatMap(item => Object.entries(item))
                .map(([name, share]) => `${name} ${Number(share).toFixed(0)}%`)
                .join(', ');
        });

        const availableOptions = (row: IMixtureRow, index: number): string[] => {
            const fromParam = Array.isArray(props.param?.all_values) ? props.param.all_values : [];
            const all = fromParam.length ? fromParam : props.mediaOptions;
            const taken = rows.value
                .filter((r, i) => i !== index)
                .map(r => r.name)
                .filter(Boolean);
            const options = all.filter(name => row.name === name || !taken.includes(name));
            return Array.from(new Set(options));
        }

        const sum = computed<number>(() => {
            return rows.value.reduce((acc, row) => acc + (row.share || 0), 0);
        });

        const mustTwoMedia = computed<boolean>(() => {
            return rows.value.filter(r => r.name && r.share !== null).length < 2;
        });

        const isValid = computed<boolean>(() => {
            if (mustTwoMedia.value) return false;
            return Math.abs(sum.value - 100) < 0.0001;
        });

        const canAddRow = computed<boolean>(() => {
            if (sum.value >= 100 - 0.0001) return false;
            const hasAvailable = rows.value.length === 0
                || availableOptions({ name: '', share: null } as IMixtureRow, -1).length > 0;
            return hasAvailable;
        });

        const openEditor = () => {
            rows.value = fromComposition(currentComposition.value);
            editorVisible.value = true;
        }

        const closeEditor = () => {
            editorVisible.value = false;
        }

        const addRow = () => {
            rows.value.push({ name: '', share: null });
        }

        const removeRow = (index: number) => {
            if (rows.value.length <= 1) return;
            rows.value.splice(index, 1);
        }

        const applyComposition = () => {
            if (!isValid.value) return;
            const composition = rows.value
                .filter(r => r.name && r.share !== null)
                .map(r => ({ [r.name]: Number(r.share) }));
            emit('valueChanged', composition);
            closeEditor();
        }

        watch(() => props.modelValue, () => {
            if (!editorVisible.value) {
                rows.value = fromComposition(currentComposition.value);
            }
        }, { deep: true })

        return {
            editorVisible,
            rows,
            parseShare,
            currentLabel,
            availableOptions,
            sum,
            mustTwoMedia,
            isValid,
            canAddRow,
            openEditor,
            closeEditor,
            addRow,
            removeRow,
            applyComposition,
        };
    },
});
</script>