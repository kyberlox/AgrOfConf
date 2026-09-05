<template>
<div v-if="showModal"
     class="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
    <div class="bg-white rounded-lg p-6 w-full max-w-md shadow-xl">
        <h1 class="text-lg font-medium mb-4">Создание параметра</h1>

        <div class="flex flex-col gap-3">
            <label class="flex flex-col gap-1 text-sm">
                <span class="text-gray-700">Название</span>
                <input class="input-param w-full"
                       v-model="form.name"
                       placeholder="Название параметра" />
            </label>

            <label class="flex flex-col gap-1 text-sm">
                <span class="text-gray-700">Тип</span>
                <select class="input-param w-full"
                        v-model="form.type">
                    <option value="Table">Табличный</option>
                    <option value="Formula">Формульный</option>
                    <option value="Drawing">Файл</option>
                </select>
            </label>

            <label v-if="form.type != 'Drawing'" class="flex flex-col gap-1 text-sm">
                <span class="text-gray-700">Тип ввода</span>
                <select class="input-param w-full"
                        v-model="form.required_type">
                    <option value="list">Выбор из списка</option>
                    <option value="user_input">Ручной ввод</option>
                    <option value="select-input">Выбор + ввод</option>
                </select>
            </label>

            <template v-if="form.type == 'Table'">
                <label class="flex flex-col gap-1 text-sm">
                    <span class="text-gray-700">Таблица (таблица, в которую добавить колонку)</span>
                    <input class="input-param w-full"
                           v-model="form.table_name"
                           list="product-tables-list"
                           placeholder="имя_таблицы" />
                    <datalist id="product-tables-list">
                        <option v-for="t in tables"
                                :key="t"
                                :value="t">{{ t }}</option>
                    </datalist>
                </label>
            </template>

            <template v-else-if="form.type == 'Formula'">
                <label class="flex flex-col gap-1 text-sm">
                    <span class="text-gray-700">Функция расчёта</span>
                    <input class="input-param w-full"
                           v-model="form.func"
                           list="formula-algorithms"
                           placeholder="например count_A" />
                    <datalist id="formula-algorithms">
                        <option v-for="f in algorithms"
                                :key="f"
                                :value="f">{{ f }}</option>
                    </datalist>
                </label>
                <label class="flex flex-col gap-1 text-sm">
                    <span class="text-gray-700">Функция валидации</span>
                    <input class="input-param w-full"
                           v-model="form.validate"
                           list="formula-validators"
                           placeholder="например validate_nonzero" />
                    <datalist id="formula-validators">
                        <option v-for="f in validators"
                                :key="f"
                                :value="f">{{ f }}</option>
                    </datalist>
                </label>
            </template>

            <template v-if="form.type == 'Drawing'">
                <label class="flex flex-col gap-1 text-sm">
                    <span class="text-gray-700">Функция выбора файла (новая система формул)</span>
                    <input class="input-param w-full"
                           v-model="form.func"
                           list="formula-algorithms"
                           placeholder="например file_by_construction" />
                    <datalist id="formula-algorithms">
                        <option v-for="f in algorithms"
                                :key="f"
                                :value="f">{{ f }}</option>
                    </datalist>
                </label>
            </template>
        </div>

        <div class="flex justify-end gap-3 mt-5">
            <button class="px-4 py-2 rounded bg-gray-200 hover:bg-gray-300"
                    @click="$emit('closeModal')">
                Назад
            </button>
            <button class="px-4 py-2 rounded text-white bg-orange-500 hover:bg-orange-600 disabled:opacity-50"
                    :disabled="!form.name || isLoading"
                    @click="submit">
                {{ isLoading ? '...' : 'Создать' }}
            </button>
        </div>
    </div>
</div>
</template>
<script lang='ts'>
import { defineComponent, onMounted, reactive, ref, watch } from 'vue';
import Api from '@/utils/Api';

interface IParamForm {
    name: string,
    type: 'Table' | 'Formula' | 'Drawing',
    required_type: string,
    table_name: string,
    func: string,
    validate: string,
    drawing_of: string,
    use_first_chars: number
}

const emptyForm = (): IParamForm => ({
    name: '',
    type: 'Table',
    required_type: 'list',
    table_name: '',
    func: '',
    validate: '',
    drawing_of: '',
    use_first_chars: 0
});

export default defineComponent({
    props: {
        showModal: { type: Boolean, default: false },
        productId: { type: [Number, String], required: true },
        tables: { type: Array as () => string[], default: () => [] },
        isLoading: { type: Boolean }
    },
    emits: ['closeModal', 'created'],
    setup(props, { emit }) {
        const form = reactive<IParamForm>(emptyForm());
        const algorithms = ref<string[]>([]);
        const validators = ref<string[]>([]);

        onMounted(async () => {
            try {
                const data = await Api.get('formula_functions')
                algorithms.value = data?.algorithms ?? []
                validators.value = data?.validators ?? []
            } catch (e) {
                console.error(e)
            }
        })

        watch(() => props.showModal, () => {
            Object.assign(form, emptyForm())
        })

        const submit = async () => {
            const body: Record<string, unknown> = {
                name: form.name,
                type: form.type,
                description: '',
                measuring_unit: null,
                visibility: true,
                required_type: form.type == 'Drawing' ? 'drawing' : form.required_type,
                table_name: form.type == 'Table' ? form.table_name : null,
                field_of_view: null,
                product_id: Number(props.productId),
                sort: 0
            }
            if (form.type == 'Formula') {
                body.formula_config = {
                    func: form.func,
                    validate: form.validate || undefined,
                    type: 'formula'
                }
            }
            if (form.type == 'Drawing') {
                body.formula_config = {
                    type: 'drawing',
                    // Функция, возвращающая URL файла по значению зависимого параметра.
                    func: form.func || undefined
                }
            }
            try {
                await Api.post('parameters/', body)
                emit('created')
                emit('closeModal')
            } catch (e) {
                console.error('Не удалось создать параметр:', e)
            }
        }

        return {
            form,
            algorithms,
            validators,
            submit
        }
    }
});
</script>