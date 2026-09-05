<template>
<SlotModal @closeModal="$emit('closeModal')">
    <div class="flex flex-col w-full gap-[18px] min-w-[750px] p-[16px]">
        <h3 class="text-lg font-medium">Настройки параметра «{{ parameter?.name }}»</h3>

        <BaseInput v-for="(item, index) in [{ title: 'Название', name: 'name' }, { name: 'description', title: 'Описание' }]"
                   :inputSettings="initInputProps(item)"
                   :key="'navGroup' + index"
                   @value-changed="(value: string) => changeValue(value, (item.name as 'name' | 'description'))" />

        <div class="flex flex-col gap-[8px]">
            <label class="text-sm text-gray-700">Единица измерения</label>
            <input class="input-param w-full"
                   :value="newParameter.measuring_unit"
                   placeholder="например мм, кгс/см²"
                   @input="newParameter.measuring_unit = ($event.target as HTMLInputElement).value" />
        </div>

        <div class="flex flex-row gap-[24px] flex-wrap">
            <label class="flex flex-row items-center gap-[8px] text-sm text-gray-700 cursor-pointer">
                <input type="checkbox" v-model="newParameter.visibility" />
                Видим для пользователя
            </label>
            <label class="flex flex-row items-center gap-[8px] text-sm text-gray-700 cursor-pointer">
                <input type="checkbox" v-model="newParameter.editable" />
                Редактируемый пользователем
            </label>
        </div>

        <div class="flex flex-col gap-[8px]">
            <label class="text-sm text-gray-700">Тип данных (required_type)</label>
            <select class="input-param w-full" v-model="newParameter.required_type">
                <option value="list">Список (select)</option>
                <option value="user_input">Ввод текста (user_input)</option>
            </select>
        </div>

        <!-- Поля новой системы формул (для расчётных параметров) -->
        <template v-if="parameter?.type == 'Formula'">
            <div class="flex flex-col gap-[8px]">
                <label class="text-sm text-gray-700">Функция расчёта</label>
                <input class="input-param w-full"
                       list="formula-algorithms"
                       :value="formulaConfig.func"
                       placeholder="например count_A"
                       @input="changeValue(($event.target as HTMLInputElement).value, 'func')" />
                <datalist id="formula-algorithms">
                    <option v-for="f in algorithms"
                            :key="f"
                            :value="f">{{ f }}</option>
                </datalist>
            </div>
            <div class="flex flex-col gap-[8px]">
                <label class="text-sm text-gray-700">Функция валидации</label>
                <input class="input-param w-full"
                       list="formula-validators"
                       :value="formulaConfig.validate"
                       placeholder="например validate_nonzero"
                       @input="changeValue(($event.target as HTMLInputElement).value, 'validate')" />
                <datalist id="formula-validators">
                    <option v-for="f in validators"
                            :key="f"
                            :value="f">{{ f }}</option>
                </datalist>
            </div>
        </template>

        <!-- Конфигурация параметра-файла -->
        <template v-if="parameter?.type == 'Drawing'">
            <div class="flex flex-col gap-[8px]">
                <label class="text-sm text-gray-700">Функция выбора файла</label>
                <input class="input-param w-full"
                       list="formula-algorithms"
                       :value="formulaConfig.func"
                       placeholder="например file_by_construction"
                       @input="changeValue(($event.target as HTMLInputElement).value, 'func')" />
                <datalist id="formula-algorithms">
                    <option v-for="f in algorithms"
                            :key="f"
                            :value="f">{{ f }}</option>
                </datalist>
            </div>

            <!-- Файлы параметра (выступают как его значения) -->
            <div class="flex flex-col gap-[8px]">
                <label class="text-sm text-gray-700">Файлы параметра</label>
                <div v-if="files.length" class="flex flex-col gap-[6px]">
                    <div v-for="f in files"
                         :key="f.id"
                         class="flex flex-row items-center justify-between gap-[12px] text-sm">
                        <div class="flex flex-row items-center gap-[8px] min-w-0">
                            <img v-if="isImage(f.name) && f.file_url"
                                 :src="fileUrl(f.file_url)"
                                 class="h-10 w-10 object-contain rounded border border-gray-200"
                                 alt="" />
                            <span class="truncate">{{ f.name }}</span>
                        </div>
                        <button class="text-red-500 hover:text-red-700"
                                @click="removeFile(f)">Удалить</button>
                    </div>
                </div>
                <input type="file"
                       multiple
                       class="input-param"
                       @change="uploadFiles" />
            </div>
        </template>

        <div class="flex flex-row justify-end gap-[15px]">
            <div v-for="(item, index) in ['Назад', 'Принять']"
                 :key="'bread' + index">
                <BaseButton class="min-w-[200px]"
                            :buttonSettings="{ class: item == 'Назад' ? 'button-secondary' : 'button-primary', disabled: item == 'Назад' ? false : disabled }"
                            @click="item == 'Назад' ? $emit('closeModal') : applyParameter()">
                    <span>{{ item }}</span>
                </BaseButton>
            </div>
        </div>
    </div>
</SlotModal>
</template>

<script lang='ts'>
import SlotModal from '@/components/layout/SlotModal.vue';
import { defineComponent, onMounted, ref, type PropType, computed } from 'vue';
import type { IParameter } from '@/assets/interfaces/IParameter';
import { BaseButton, BaseInput } from 'beans-ui-kit';
import Api from '@/utils/Api';
import { fileUrl } from '@/utils/fileUrl';

export default defineComponent({
    components: {
        SlotModal,
        BaseInput,
        BaseButton
    },
    emits: ['closeModal', 'updateParameter'],
    props: {
        parameter: {
            type: Object as PropType<IParameter>
        },
        disabled: {
            type: Boolean
        }
    },
    setup(props, { emit }) {
        const initialConfig = computed<{ func: string, validate: string }>(() => {
            const cfg = props.parameter?.formula_config;
            if (cfg && typeof cfg === 'object') {
                return {
                    func: String(cfg.func ?? ''),
                    validate: String(cfg.validate ?? '')
                }
            }
            return { func: '', validate: '' }
        })

        const newParameter = ref<{
            name: string,
            description: string,
            measuring_unit: string,
            visibility: boolean,
            editable: boolean,
            required_type: string,
            formula_config?: Record<string, unknown>
        }>({
            name: props.parameter?.name ?? '',
            description: props.parameter?.description ?? '',
            measuring_unit: props.parameter?.measuring_unit ?? '',
            visibility: props.parameter?.visibility ?? true,
            editable: props.parameter?.editable ?? true,
            required_type: props.parameter?.required_type ?? 'list',
            formula_config: { ...initialConfig.value }
        });

        const algorithms = ref<string[]>([]);
        const validators = ref<string[]>([]);

        const files = ref<Array<{ id: number; name: string; file_url: string }>>([]);

        const isImage = (name: string) => /\.(png|jpe?g|gif|webp|svg)$/i.test(name);

        const loadFiles = async () => {
            if (!props.parameter?.id) return
            try {
                const data = await Api.get(`parameters/${props.parameter.id}/files`)
                files.value = data ?? []
            } catch (e) {
                console.error('Не удалось загрузить файлы параметра:', e)
            }
        }

        const uploadFiles = async (e: Event) => {
            const input = e.target as HTMLInputElement
            if (!input.files?.length || !props.parameter?.id) return
            const fd = new FormData()
            Array.from(input.files).forEach(file => fd.append('files', file))
            try {
                await Api.post(`parameters/${props.parameter.id}/files`, fd)
                input.value = ''
                await loadFiles()
            } catch (err) {
                console.error('Не удалось загрузить файлы:', err)
            }
        }

        const removeFile = async (f: { id: number }) => {
            if (!props.parameter?.id) return
            try {
                await Api.delete(`parameters/${props.parameter.id}/files/${f.id}`)
                await loadFiles()
            } catch (err) {
                console.error('Не удалось удалить файл:', err)
            }
        }

        onMounted(async () => {
            try {
                const data = await Api.get('formula_functions')
                algorithms.value = data?.algorithms ?? []
                validators.value = data?.validators ?? []
            } catch (e) {
                console.error('Не удалось получить список функций:', e)
            }
            if (props.parameter?.type == 'Drawing') {
                await loadFiles()
            }
        })

        const formulaConfig = computed(() => ({
            func: String(newParameter.value.formula_config?.func ?? ''),
            validate: String(newParameter.value.formula_config?.validate ?? '')
        }))

        const drawingConfig = computed(() => ({
            drawing_of: String(newParameter.value.formula_config?.drawing_of ?? ''),
            use_first_chars: String(newParameter.value.formula_config?.use_first_chars ?? '')
        }))

        const setDrawingConfig = (key: 'drawing_of' | 'use_first_chars', value: string) => {
            newParameter.value.formula_config = {
                ...(newParameter.value.formula_config || {}),
                [key]: key === 'use_first_chars' ? Number(value) || 0 : value,
                type: 'drawing'
            }
        }

        const changeValue = (value: string, key: 'name' | 'description' | 'func' | 'validate') => {
            if (key === 'func' || key === 'validate') {
                newParameter.value.formula_config = {
                    ...(newParameter.value.formula_config || {}),
                    [key]: value
                }
            } else {
                newParameter.value[key] = value
            }
        }

        const initInputProps = (item: { title: string, name: string }) => {
            return {
                class: 'input-param',
                label: item.title,
                value: item.name == 'name' ? props.parameter?.name : props.parameter?.description,
                placeholder: '...'
            }
        }

        const applyParameter = () => {
            const fc = newParameter.value.formula_config || {}
            const hasConfig = !!(fc.func || fc.validate || fc.drawing_of)
            emit('updateParameter', props.parameter?.id, {
                name: newParameter.value.name,
                description: newParameter.value.description,
                measuring_unit: newParameter.value.measuring_unit,
                visibility: newParameter.value.visibility,
                editable: newParameter.value.editable,
                required_type: newParameter.value.required_type,
                ...(hasConfig ? { formula_config: fc } : {})
            })
        }

        return {
            newParameter,
            formulaConfig,
            drawingConfig,
            algorithms,
            validators,
            files,
            isImage,
            fileUrl,
            uploadFiles,
            removeFile,
            changeValue,
            setDrawingConfig,
            initInputProps,
            applyParameter
        }
    }
});
</script>