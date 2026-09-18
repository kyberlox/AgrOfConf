<template>
<div class="min-h-[86vh] bg-white rounded-lg w-full p-[16px]">
    <div class="flex flex-row justify-start gap-[25px] flex-wrap">
        <div class="max-w-full lg:max-w-[40%] p-4 bg-blue-50 border border-blue-200 rounded-lg shadow-sm">
            <div class="text-lg text-blue-800 font-medium mb-2 grow">
                Информация о редактировании
            </div>
            <div class="text-md text-gray-700">
                Для изменения логики подбора по табличным параметрам необходимо отредактировать
                исходный excel файл, сперва скачав его, отредактировав и затем загрузив по
                кнопкам в блоке Excel, добавить или отредактировать формульные параметры можно
                по нажатию на блок или кнопку "+"
            </div>
        </div>
        <div class="flex justify-start gap-2">
            <div
                 class="flex flex-row flex-wrap md:flex-nowrap gap-2 items-center border border-green-300 bg-green-100 rounded-md p-4">
                <div class="text-lg w-full">Excel</div>
                <BaseButton :buttonSettings="{ class: 'button-primary', disabled: excelDownloading }"
                            @click="downloadExcel">
                    <Loader v-if=excelDownloading
                            class="button-primary__loader" />
                    <span v-else>Скачать</span>
                </BaseButton>

                <VInputFile :buttonClass="'button-primary'"
                            :needFileNameInTitle="false"
                            :isLoading="excelUploading"
                            @fileUpload="(file) => handleExcelUpload(file)" />
            </div>
        </div>
        <div class="flex justify-start gap-2">
            <div
                 class="flex flex-row flex-wrap md:flex-nowrap gap-2 items-center border border-indigo-300 bg-indigo-100 rounded-md p-4">
                <div class="text-lg w-full">Перенос конфигурации</div>
                <BaseButton :buttonSettings="{ class: 'button-primary', disabled: exporting }"
                            @clicked="exportProduct">
                    <Loader class="button-primary__loader"
                            v-if="exporting" />
                    <span v-else>Экспорт</span>
                </BaseButton>
                <VInputFile :buttonClass="'button-primary'"
                            :needFileNameInTitle="false"
                            :fileName="'Импорт'"
                            :isLoading="importing"
                            @fileUpload="handleImportFile" />
            </div>
        </div>
        <div class="w-fit m-auto">
            <Transition name="fade-btn">
                <BaseButton v-if="sortChanged"
                            class="button-primary__loader"
                            :buttonSettings="{ class: 'button-primary' }"
                            @clicked="sendNewSort">
                    Принять сортировку
                </BaseButton>
            </Transition>
        </div>
    </div>
    <div class="flex flex-row items-center justify-start gap-[15px]">
        <div class="mt-[20px] max-w-[250px] w-[250px]"
             v-for="item in actionButtons"
             :key="item.name">
            <BaseButton :buttonSettings="{ class: 'button-secondary' }"
                        @clicked="handleActionButton(item.name)">
                {{ item.title }}
            </BaseButton>
        </div>
        <div class="mt-[20px] max-w-[250px] w-[250px]">
            <BaseButton :buttonSettings="{ class: 'button-primary' }"
                        @clicked="createParamModalVisible = true">
                Создать параметр
            </BaseButton>
        </div>
    </div>

    <!-- Статистика подборов по продукту -->
    <div class="mt-[20px] border border-gray-200 p-[20px] rounded-xl">
        <h3 class="text-lg font-medium mb-2">Статистика подборов по продукту</h3>
        <p v-if="!productStatistics.length"
           class="text-sm text-gray-500">
            Пока нет данных о подборах.
        </p>
        <ul v-else
            class="flex flex-col gap-2 max-h-[220px] overflow-auto">
            <li v-for="(s, i) in productStatistics"
                :key="i"
                class="text-sm flex flex-row justify-between gap-4 border-b border-gray-100 pb-1">
                <span>Документ №{{ s.document_number ?? "-" }}</span>
                <span>{{ s.date_search ?? "" }} — {{ s.status ?? "" }}</span>
            </li>
        </ul>
    </div>

    <!-- Блоки параметров -->
    <div class="mt-[20px]">
        <BlocksManager v-if="safeProductId !== null"
                       :productId="safeProductId"
                       @changed="getParams" />
    </div>

    <div class="flex flex-col gap-[20px]">
        <div v-if="!productTableType.length"
             class="mt-4 border border-dashed border-gray-300 p-[24px] rounded-xl text-center text-gray-500">
            <p class="text-[16px] font-medium mb-1">Параметры продукта ещё не заданы</p>
            <p class="text-sm">
                Загрузите Excel‑таблицу в блоке «excel» (кнопка загрузки) — будут созданы
                таблица и её параметры, либо создайте параметр вручную кнопкой «Создать
                параметр».
            </p>
        </div>
        <div class="flex flex-col gap-2 mt-4 border border-gray-200 p-[20px] rounded-xl"
             v-if="productTableType.length">
            <div class="flex flex-row justify-start gap-[40px] flex-wrap">
                <div v-for="item in parameterLegend"
                     :key="item.label"
                     class="flex flex-row gap-[15px]">
                    <h3 class="block">{{ item.label }}</h3>
                    <div class="w-[20px] h-[20px] rounded-md"
                         :class="item.color"></div>
                </div>
            </div>
            <div>
                <VueDraggable v-model="productTableType"
                              :animation="150"
                              target=".sort-target"
                              @start="onStart"
                              @end="onEnd">
                    <TransitionGroup type="transition"
                                     tag="ul"
                                     :name="!drag ? 'fade' : undefined"
                                     class="sort-target grid grid-cols-1 sm:grid-cols-1 md:grid-cols-1 lg:grid-cols-4 gap-4 max-w-full mt-4">
                        <ProductParameterCard v-for="parameter in productTableType"
                                              :key="parameter.id"
                                              :parameter="parameter"
                                              @delete="deleteParam"
                                              @edit="changeSettings" />
                    </TransitionGroup>
                </VueDraggable>
            </div>
        </div>
    </div>
    <ParameterSettings v-if="productSettingsVisible && selectedParameter"
                       :parameter="selectedParameter"
                       :disabled="parameterUpdating"
                       @updateParameter="(id, parameter) => updateParameter(id, parameter)"
                       @closeModal="closeParameterSettings" />

    <UploadedOl v-if="id"
                :id="id"
                :isOpen="olListModalOpen"
                :olList="olList"
                :olIsLoading="olIsLoading"
                @closeModal="olListModalOpen = false"
                @updateOlList="uploadOl"
                @removeOl="removeOl" />

    <TablesManageModal v-if="tablesModalIsOpen"
                       :tables="Array.from(productTablesList)"
                       @closeModal="tablesModalIsOpen = false"
                       @deleteTable="deleteTableFromProduct" />

    <CertificatesModal v-if="id"
                       :id="id"
                       :isOpen="filesModalIsOpen"
                       :filesList="filesList"
                       :isLoading="filesIsLoading"
                       @closeModal="filesModalIsOpen = false"
                       @updateFilesList="uploadFile"
                       @removeFile="removeFile" />

    <CreateParameterModal v-if="safeProductId !== null"
                          :showModal="createParamModalVisible"
                          :productId="safeProductId"
                          :tables="productTablesList"
                          @closeModal="createParamModalVisible = false"
                          @created="getParams" />

    <PromptEditBlock :id="Number(id)"
                     :params="productTableType" />

</div>
</template>
<script lang="ts">
import Api from '@/utils/Api'
import { defineComponent, onMounted, ref, computed, TransitionGroup, nextTick } from 'vue'
import download from 'downloadjs'
import { BaseButton } from 'beans-ui-kit'
import { VueDraggable } from 'vue-draggable-plus'
import ParameterSettings from './ParameterSettingsModal.vue'
import type { IParameter } from '@/assets/interfaces/IParameter'
import UploadedOl from './UploadedOlModal.vue'
import { getTkpVariants } from '@/utils/getTkpVariants.ts'
import { type ITkpVariant } from '@/assets/interfaces/ITkpVariant.ts'
import { toast } from 'vue3-toastify'
import Loader from '@/components/layout/Loader.vue'
import VInputFile from '@/components/layout/VInputFile.vue'
import TablesManageModal from './TablesManageModal.vue'
import CreateParameterModal from './CreateParameterModal.vue'
import BlocksManager from './BlocksManager.vue'
import CertificatesModal from './CertificatesModal.vue'
import { getProductFiles } from '@/utils/getProductFiles.ts'
import { type IProductFile } from '@/assets/interfaces/IProductFile.ts'
import ProductParameterCard from './components/ProductParameterCard.vue'
import PromptEditBlock from './components/PromptEditBlock.vue';

interface ProductStatistic {
    document_number?: string | number
    date_search?: string
    status?: string
}

const actionButtons = [
    { name: 'tkp', title: 'Загруженные ТКП' },
    { name: 'tables', title: 'Загруженные таблицы' },
    { name: 'files', title: 'Сертификаты' },
] as const

const parameterLegend = [
    { label: 'Табличные параметры', color: 'bg-green-200' },
    { label: 'Формульные параметры', color: 'bg-blue-200' },
] as const

export default defineComponent({
    components: {
        BaseButton,
        TransitionGroup,
        VueDraggable,
        ParameterSettings,
        UploadedOl,
        Loader,
        VInputFile,
        TablesManageModal,
        CreateParameterModal,
        BlocksManager,
        CertificatesModal,
        ProductParameterCard,
        PromptEditBlock,
    },
    props: {
        id: {
            type: String,
            required: true,
        },
    },
    setup(props) {
        const productTableType = ref<IParameter[]>([])
        const drag = ref(false)
        const sortChanged = ref(false)
        const productSettingsVisible = ref(false)
        const idInSettings = ref<number | false>()
        const parameterUpdating = ref(false)
        const olListModalOpen = ref(false)
        const olList = ref<ITkpVariant[]>([])
        const olIsLoading = ref(false)
        const excelDownloading = ref(false)
        const excelUploading = ref(false)
        const exporting = ref(false)
        const importing = ref(false)
        const tablesModalIsOpen = ref(false)
        const productTablesList = ref<string[]>([])
        const createParamModalVisible = ref(false)
        const productStatistics = ref<ProductStatistic[]>([])
        const filesModalIsOpen = ref(false)
        const filesList = ref<IProductFile[]>([])
        const filesIsLoading = ref(false)
        const selectedParameter = computed(() =>
            productTableType.value.find((parameter) => parameter.id === idInSettings.value),
        )

        const downloadExcel = async () => {
            try {
                excelDownloading.value = true
                const response = await Api.post(
                    `tables/download_xlsx?product_id=${props.id}`,
                    undefined,
                    { responseType: 'blob' },
                    undefined,
                    true,
                )
                const contentDisposition = response.headers['content-disposition']
                const filename = contentDisposition?.split('filename=')[1].replaceAll('"', '')
                download(response.data, String(filename))
            } catch (error) {
                console.error(error)
            } finally {
                excelDownloading.value = false
            }
        }

        const handleExcelUpload = async (file: File) => {
            excelUploading.value = true
            const body = new FormData()
            body.append('file', file)
            try {
                await Api.post(`tables/upload_xlsx?product_id=${props.id}`, body)
            } catch (error) {
                console.error('excelUpload', error)
            } finally {
                excelUploading.value = false
                getParams()
            }
        }

        const exportProduct = async () => {
            exporting.value = true
            try {
                const blob = await Api.get(`products/${props.id}/export`, { responseType: 'blob' })
                const filename = `product_${props.id}.zip`
                download(blob, filename)
            } catch (error) {
                console.error('exportProduct', error)
            } finally {
                exporting.value = false
            }
        }

        const handleImportFile = async (file: File) => {
            if (!file) return
            const fd = new FormData()
            fd.append('archive', file)
            importing.value = true
            try {
                const data = await Api.post('products/import', fd)
                if (data && data.id) {
                    toast.success(`Продукт импортирован (id=${data.id})`)
                    window.location.href = `/admin/product/${data.id}`
                }
            } catch (error) {
                console.error('importProduct', error)
                toast.error('Ошибка импорта')
            } finally {
                importing.value = false
            }
        }

        const getParams = async () => {
            try {
                const products = (await Api.get(`parameters/by_product/${props.id}`)) as
                    | IParameter[]
                    | undefined
                if (!Array.isArray(products)) {
                    productTableType.value = []
                    productTablesList.value = []
                } else {
                    productTableType.value = [...products].sort((a, b) => a.sort - b.sort)
                    productTablesList.value = Array.from(
                        new Set(
                            products.map((e) => e.table_name).filter((name): name is string => Boolean(name)),
                        ),
                    )
                }
            } catch {
                productTableType.value = []
            }
        }

        const loadProductStatistics = async () => {
            if (!props.id || props.id === 'null') {
                productStatistics.value = []
                return
            }
            try {
                const data = await Api.get(`selection_statistic/selection?product_id=${props.id}`)
                productStatistics.value = Array.isArray(data) ? data : (data?.data ?? [])
            } catch {
                productStatistics.value = []
            }
        }

        const safeProductId = computed(() => {
            const id = Number(props.id)
            return Number.isFinite(id) ? id : null
        })

        onMounted(async () => {
            getParams()
            getOlList()
            getFilesList()
            loadProductStatistics()
        })

        const getOlList = async () => {
            if (props.id) olList.value = (await getTkpVariants(props.id)) || []
        }

        const getFilesList = async () => {
            if (props.id) filesList.value = (await getProductFiles(props.id)) || []
        }

        const deleteParam = async (id: number) => {
            if (!window.confirm('Удалить параметр? Это действие нельзя отменить.')) return
            try {
                await Api.delete(`parameters/${id}`)
                await getParams()
            } catch (error) {
                console.error('deleteParam', error)
            }
        }

        const onStart = () => {
            sortChanged.value = true
            drag.value = true
        }

        const onEnd = () => {
            nextTick(() => {
                drag.value = false
                // Сохраняем новый порядок параметров сразу после перетаскивания,
                // чтобы он влиял на порядок в подборе.
                sendNewSort()
            })
        }

        const sendNewSort = async () => {
            sortChanged.value = false
            const newBody = productTableType.value.map((e, index) => {
                e.sort = index + 1
                return e
            })
            await Api.put(`/parameters/sort/${props.id}`, newBody)
        }

        const changeSettings = (id: number) => {
            productSettingsVisible.value = true
            idInSettings.value = id
        }

        const closeParameterSettings = () => {
            productSettingsVisible.value = false
            idInSettings.value = false
        }

        const updateParameter = async (id: number, parameter: Record<string, unknown>) => {
            parameterUpdating.value = true
            try {
                await Api.put(`parameters/${id}`, parameter)
            } finally {
                getParams()
                parameterUpdating.value = false
                productSettingsVisible.value = false
            }
        }

        const removeOl = async (id: number) => {
            try {
                await Api.delete(`tkp_generation/delete/${id}`)
                await getOlList()
            } catch (error) {
                console.error(error)
            }
        }

        const uploadOl = async (fileFormData: FormData) => {
            olIsLoading.value = true
            try {
                const data = await Api.post('tkp_generation/add', fileFormData)
                if (data) {
                    toast.success('ТКП успешно загружено')
                }
                await getOlList()
            } catch (error) {
                console.error(error)
            } finally {
                olIsLoading.value = false
            }
        }

        const deleteTableFromProduct = async (tableName: string) => {
            try {
                await Api.delete(`tables/${props.id}/${tableName}`)
                await getParams()
            } catch (error) {
                console.error(error)
            }
        }

        const handleActionButton = (name: string) => {
            if (name == 'tkp') olListModalOpen.value = true
            else if (name == 'tables') tablesModalIsOpen.value = true
            else if (name == 'files') filesModalIsOpen.value = true
        }

        const removeFile = async (id: number) => {
            try {
                await Api.delete(`products/delete_product_file/${id}`)
                await getFilesList()
            } catch (error) {
                console.error(error)
            }
        }

        const uploadFile = async (fileFormData: FormData) => {
            filesIsLoading.value = true
            try {
                const data = await Api.post('products/upload_product_file', fileFormData)
                if (data) {
                    toast.success('Сертификат успешно загружен')
                }
                await getFilesList()
            } catch (error) {
                console.error(error)
            } finally {
                filesIsLoading.value = false
            }
        }

        return {
            productTableType,
            createParamModalVisible,
            productStatistics,
            loadProductStatistics,
            getParams,
            safeProductId,
            selectedParameter,
            sortChanged,
            drag,
            productSettingsVisible,
            idInSettings,
            parameterUpdating,
            olList,
            olListModalOpen,
            olIsLoading,
            excelUploading,
            tablesModalIsOpen,
            excelDownloading,
            exporting,
            importing,
            handleImportFile,
            productTablesList,
            actionButtons,
            parameterLegend,
            removeOl,
            getFilesList,
            filesList,
            filesModalIsOpen,
            filesIsLoading,
            removeFile,
            uploadFile,
            handleActionButton,
            downloadExcel,
            sendNewSort,
            handleExcelUpload,
            exportProduct,
            deleteParam,
            onStart,
            onEnd,
            changeSettings,
            closeParameterSettings,
            updateParameter,
            uploadOl,
            deleteTableFromProduct,
        }
    },
})
</script>

<style>
.fade-move,
.fade-enter-active,
.fade-leave-active {
    transition: all 0.5s cubic-bezier(0.55, 0, 0.1, 1);
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
    transform: scaleY(0.01) translate(30px, 0);
}

.fade-leave-active {
    position: absolute;
}

.fade-btn-enter-active,
.fade-btn-leave-active {
    transition: opacity 0.3s ease;
}

.fade-btn-enter-from,
.fade-btn-leave-to {
    opacity: 0;
}
</style>
