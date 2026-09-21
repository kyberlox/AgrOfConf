<template>
    <SlotModal v-if="showModal" @closeModal="$emit('closeModal')">
        <div class="bg-white rounded-lg p-6 w-full max-w-md shadow-xl">
            <h1 class="text-lg font-medium mb-4">Создание параметра</h1>

            <div class="flex flex-col gap-3">
                <label class="flex flex-col gap-1 text-sm">
                    <span class="text-gray-700">Название</span>
                    <input class="input-param w-full" v-model="form.name" placeholder="Название параметра" />
                </label>

                <label class="flex flex-col gap-1 text-sm">
                    <span class="text-gray-700">Тип</span>
                    <select class="input-param w-full" v-model="form.type">
                        <option value="Table">Табличный</option>
                        <option value="Formula">Формульный</option>
                        <option value="Drawing">Файл</option>
                        <option value="FormulaMix">Состав смеси</option>
                    </select>
                </label>

                <div v-if="form.type == 'FormulaMix'" class="text-xs text-gray-500">
                    Параметр состава смеси. В конфигураторе для него откроется попап-редактор: выбор рабочих сред и их
                    мольных долей (двух сред и более, сумма долей = 100%).
                </div>

                <label v-if="form.type != 'Drawing' && form.type != 'FormulaMix'" class="flex flex-col gap-1 text-sm">
                    <span class="text-gray-700">Тип ввода</span>
                    <select class="input-param w-full" v-model="form.required_type">
                        <option value="list">Выбор из списка</option>
                        <option value="user_input">Ручной ввод</option>
                        <option value="select-input">Выбор + ввод</option>
                        <option value="checkbox">Чекбокс (Смесь)</option>
                    </select>
                </label>

                <label class="flex flex-row items-center gap-2 text-sm text-gray-700 cursor-pointer">
                    <input type="checkbox" v-model="form.special" />
                    Специальный (отображать отдельным блоком справа)
                </label>

                <template v-if="form.type == 'Table'">
                    <label class="flex flex-col gap-1 text-sm">
                        <span class="text-gray-700">Таблица (таблица, в которую добавить колонку)</span>
                        <input
                            class="input-param w-full"
                            v-model="form.table_name"
                            list="product-tables-list"
                            placeholder="имя_таблицы" />
                        <datalist id="product-tables-list">
                            <option v-for="t in tables" :key="t" :value="t">{{ t }}</option>
                        </datalist>
                    </label>
                </template>

                <template v-else-if="form.type == 'Formula'">
                    <label v-for="field in formulaFields" :key="field.model" class="flex flex-col gap-1 text-sm">
                        <span class="text-gray-700">{{ field.label }}</span>
                        <input
                            v-model="form[field.model]"
                            class="input-param w-full"
                            :list="field.listId"
                            :placeholder="field.placeholder" />
                        <datalist :id="field.listId">
                            <option v-for="option in field.options" :key="option" :value="option">
                                {{ option }}
                            </option>
                        </datalist>
                    </label>
                    <ValuesListEditor
                        v-if="['list', 'select-input'].includes(form.required_type)"
                        :values="form.values"
                        @update:values="(v: string[]) => (form.values = v)" />
                </template>

                <template v-if="form.type == 'Drawing'">
                    <label class="flex flex-col gap-1 text-sm">
                        <span class="text-gray-700">Функция выбора файла (новая система формул)</span>
                        <input
                            class="input-param w-full"
                            v-model="form.func"
                            list="formula-algorithms"
                            placeholder="например file_by_construction" />
                        <datalist id="formula-algorithms">
                            <option v-for="f in algorithms" :key="f" :value="f">{{ f }}</option>
                        </datalist>
                    </label>
                </template>
            </div>

            <div class="flex justify-end gap-3 mt-5">
                <button class="px-4 py-2 rounded bg-gray-200 hover:bg-gray-300" @click="$emit('closeModal')">
                    Назад
                </button>
                <button
                    class="px-4 py-2 rounded text-white bg-orange-500 hover:bg-orange-600 disabled:opacity-50"
                    :disabled="!form.name || isLoading"
                    @click="submit">
                    {{ isLoading ? "..." : "Создать" }}
                </button>
            </div>
        </div>
    </SlotModal>
</template>
<script lang="ts">
import { computed, defineComponent, watch, ref } from "vue";
import Api from "@/utils/Api";
import ValuesListEditor from "./ValuesListEditor.vue";
import SlotModal from "@/components/layout/SlotModal.vue";
import { useFormulaFunctions } from "@/composables/useFormulaFunctions";

interface IParamForm {
    name: string;
    type: "Table" | "Formula" | "Drawing" | "FormulaMix";
    required_type: string;
    table_name: string;
    func: string;
    validate: string;
    values: string[];
    drawing_of: string;
    use_first_chars: number;
    special: boolean;
}

const emptyForm = (): IParamForm => ({
    name: "",
    type: "Table",
    required_type: "list",
    table_name: "",
    func: "",
    validate: "",
    values: [],
    drawing_of: "",
    use_first_chars: 0,
    special: false,
});

export default defineComponent({
    components: {
        ValuesListEditor,
        SlotModal,
    },
    props: {
        showModal: { type: Boolean, default: false },
        productId: { type: [Number, String], required: true },
        tables: { type: Array as () => string[], default: () => [] },
        isLoading: { type: Boolean },
    },
    emits: ["closeModal", "created"],
    setup(props, { emit }) {
        const form = ref<IParamForm>(emptyForm());
        const { algorithms, validators } = useFormulaFunctions();
        const formulaFields = computed(() => [
            {
                model: "func" as const,
                label: "Функция расчёта",
                listId: "formula-algorithms",
                placeholder: "например count_A",
                options: algorithms.value,
            },
            {
                model: "validate" as const,
                label: "Функция валидации",
                listId: "formula-validators",
                placeholder: "например validate_nonzero",
                options: validators.value,
            },
        ]);

        watch(
            () => props.showModal,
            () => {
                Object.assign(form, emptyForm());
            },
        );

        const submit = async () => {
            const body: Record<string, unknown> = {
                name: form.value.name,
                type: form.value.type,
                description: "",
                measuring_unit: null,
                visibility: true,
                required_type:
                    form.value.type == "Drawing"
                        ? "drawing"
                        : form.value.type == "FormulaMix"
                          ? "select-input"
                          : form.value.required_type,
                table_name: form.value.type == "Table" ? form.value.table_name : null,
                field_of_view: null,
                product_id: Number(props.productId),
                sort: 0,
                special: form.value.special,
            };
            if (form.value.type == "Formula") {
                body.formula_config = {
                    func: form.value.func,
                    validate: form.value.validate || undefined,
                    ...(form.value.values.length
                        ? { values: form.value.values.map((v) => v.trim()).filter(Boolean) }
                        : {}),
                    type: "formula",
                };
            }
            if (form.value.type == "Drawing") {
                body.formula_config = {
                    type: "drawing",
                    // Функция, возвращающая URL файла по значению зависимого параметра.
                    func: form.value.func || undefined,
                };
            }
            try {
                await Api.post("parameters/", body);
                emit("created");
                emit("closeModal");
            } catch (e) {
                console.error("Не удалось создать параметр:", e);
            }
        };

        return {
            form,
            algorithms,
            validators,
            formulaFields,
            submit,
        };
    },
});
</script>
