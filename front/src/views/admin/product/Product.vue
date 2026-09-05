<template>
<div class="min-h-[86vh] bg-white p-2 rounded-lg w-full p-[16px]">
    <div class="flex flex-row justify-start gap-[25px]  flex-wrap ">
        <div class="max-w-full lg:max-w-[40%] p-4 bg-blue-50 border border-blue-200 rounded-lg shadow-sm">
            <div class="text-lg text-blue-800 font-medium mb-2 grow">
                Информация о редактировании
            </div>
            <div class="text-md text-gray-700">
                Для изменения логики подбора по табличным параметрам необходимо
                отредактировать исходный
                excel
                файл, сперва скачав его, отредактировав и затем загрузив по кнопкам в блоке Excell, добавить или
                отредактировать формульные параметры можно по нажатию на блок или кнопку "+"
            </div>
        </div>
        <div class="flex justify-start gap-2">
            <div
                 class="flex flex-row flex-wrap md:flex-nowrap  gap-2 items-center border border-green-300 bg-green-100 rounded-md p-4">

                <div class="text-lg w-full">
                    Excell
                </div>
                <BaseButton :buttonSettings="{ class: 'button-primary', disabled: excellDownloading }"
                            @click="downloadExcell">
                    <Loader v-if=excellDownloading />
                    <span v-else>Скачать</span>
                </BaseButton>

                <VInputFile :buttonClass="'button-primary'"
                            :needFileNameInTitle="false"
                            :isLoading="excellUploading"
                            @fileUpload="(file) => handleExcellUpload(file)" />
            </div>
        </div>
        <div class="flex justify-start gap-2">
            <div class="flex flex-row flex-wrap md:flex-nowrap gap-2 items-center border border-indigo-300 bg-indigo-100 rounded-md p-4">
                <div class="text-lg w-full">Перенос конфигурации</div>
                <BaseButton :buttonSettings="{ class: 'button-primary', disabled: exporting }"
                            @clicked="exportProduct">
                    <Loader v-if="exporting" />
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
                            :buttonSettings="{ class: 'button=primary' }"
                            @clicked="sendNewSort">
                    Принять сортировку
                </BaseButton>
            </Transition>
        </div>
    </div>
    <div class="flex flex-row items-center justify-start gap-[15px]">
        <div class="mt-[20px] max-w-[250px] w-[250px]"
             v-for="(item, index) in actionButtons"
             :key="item.name + index">
            <BaseButton :buttonSettings="{ class: 'button-secondary' }"
                        @clicked="item.name == 'tkp' ? olListModalOpen = true : tablesModalIsOpen = true">
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
                <span>Документ №{{ s.document_number ?? '-' }}</span>
                <span>{{ s.date_search ?? '' }} — {{ s.status ?? '' }}</span>
            </li>
        </ul>
    </div>

    <!-- Блоки параметров -->
    <div class="mt-[20px]">
        <BlocksManager v-if="safeProductId"
                       :productId="safeProductId"
                       @changed="getParams" />
    </div>

    <div class="flex flex-col gap-[20px]">
        <div v-if="!productTableType.length"
             class="mt-4 border border-dashed border-gray-300 p-[24px] rounded-xl text-center text-gray-500">
            <p class="text-[16px] font-medium mb-1">Параметры продукта ещё не заданы</p>
            <p class="text-sm">
                Загрузите Excel‑таблицу в блоке «Excell» (кнопка загрузки) — будут созданы
                таблица и её параметры, либо создайте параметр вручную кнопкой «Создать параметр».
            </p>
        </div>
        <div class="flex flex-col gap-2 mt-4 border border-gray-200 p-[20px] rounded-xl"
             v-if="productTableType.length">
            <div class="flex flex-row justify-left gap-[40px] flex-wrap">
                <div v-for="item in ['Табличные параметры - ', 'Формульные параметры - ']"
                     class="flex flex-row gap-[15px]">
                    <h3 class="block">{{ item }}</h3>
                    <div class="w-[20px] h-[20px] rounded-md"
                         :class="item.includes('Табл') ? 'bg-green-200' : 'bg-blue-200'"></div>
                </div>
            </div>
            <div class="">
                <VueDraggable v-model="productTableType"
                              :animation="150"
                              target=".sort-target"
                              @start="onStart"
                              @end="onEnd">
                    <TransitionGroup type="transition"
                                     tag="ul"
                                     :name="!drag ? 'fade' : undefined"
                                     class="sort-target grid grid-cols-1 sm:grid-cols-1 md:grid-cols-1 lg:grid-cols-4 gap-4 max-w-full mt-4">
                        <li v-for="(parameter, index) in productTableType"
                            :key="parameter.id"
                            class="flex flex-col py-[20px] px-[15px]  border border-green-200 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 bg-green-50 relative cursor-move"
                            :class="{ 'bg-blue-50! border-blue-200!': parameter.type == 'Formula' }">
                            <div class="text-lg pr-[25px] font-medium  text-gray-800 mb-2 wrap-break-word">
                                {{ parameter.name }}
                            </div>
                            <div class="text-sm text-gray-600 mb-3 wrap-break-word">
                                {{ parameter.description }}
                            </div>
                            <div class="text-xs text-gray-500  wrap-break-word">
                                Из таблицы: {{ parameter.table_name }}
                            </div>
                            <div class="w-[24px] h-[24px] p-[5px] rounded-lg bg-mist-100 absolute top-[15px] right-[40px] cursor-pointer hover:bg-mist-300 text-[var(--icon-color-secondary)] hover:text-[var(--icon-color-primary)]"
                                 title="Удалить параметр"
                                 @click.stop.prevent="deleteParam(parameter.id)">
                                <CloseIcon class="text-red-500" />
                            </div>
                            <div class="w-[24px] h-[24px] p-[5px] rounded-lg bg-mist-100 absolute top-[15px] right-[15px] cursor-pointer hover:bg-mist-300 text-[var(--icon-color-secondary)] hover:text-[var(--icon-color-primary)]"
                                 @click.stop.prevent="changeSettings(parameter.id)">
                                <SettingsIcon />
                            </div>
                        </li>
                    </TransitionGroup>
                </VueDraggable>
            </div>
        </div>
    </div>
    <ParameterSettings v-if="productSettingsVisible"
                       :parameter="productTableType.find(e => e.id == idInSettings)"
                       :disabled="parameterUpdating"
                       @updateParameter="(id, parameter) => updateParameter(id, parameter)"
                       @closeModal="{ productSettingsVisible = false; idInSettings = false }" />

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

    <CreateParameterModal :showModal="createParamModalVisible"
                          :productId="safeProductId ?? ''"
                          :tables="productTablesList"
                          @closeModal="createParamModalVisible = false"
                          @created="getParams" />
</div>
</template>
<script lang='ts'>
import Api from '@/utils/Api';
import { defineComponent, onMounted, ref, computed, TransitionGroup, nextTick } from 'vue';
import SlotModal from '@/components/layout/SlotModal.vue';
import download from 'downloadjs';
import { BaseButton } from 'beans-ui-kit';
import CloseIcon from '@/assets/icons/Cross.svg?component';
import Plus from '@/assets/icons/Plus.svg?component';
import { useProductsData } from '@/stores/products';
import { startDrag, onOver, onLeave, onDrop } from '@/utils/dragEvents.ts';
import { VueDraggable } from 'vue-draggable-plus';
import SettingsIcon from '@/assets/icons/Settings.svg?component';
import ParameterSettings from './ParameterSettingsModal.vue';
import type { IParameter } from '@/assets/interfaces/IParameter';
import UploadedOl from './UploadedOlModal.vue';
import { getTkpVariants } from '@/utils/getTkpVariants.ts';
import { type ITkpVariant } from '@/assets/interfaces/ITkpVariant.ts';
import { toast } from 'vue3-toastify';
import Loader from '@/components/layout/Loader.vue';
import VInputFile from '@/components/layout/VInputFile.vue';
import TablesManageModal from './TablesManageModal.vue';
import CreateParameterModal from './CreateParameterModal.vue';
import BlocksManager from './BlocksManager.vue';

export default defineComponent({
    components: {
        SlotModal,
        BaseButton,
        CloseIcon,
        Plus,
        TransitionGroup,
        VueDraggable,
        SettingsIcon,
        ParameterSettings,
        UploadedOl,
        Loader,
        VInputFile,
        TablesManageModal,
        CreateParameterModal,
        BlocksManager
    },
    props: {
        id: {
            type: String,
            requied: true
        }
    },
    setup(props) {
        const productTableType = ref<IParameter[]>([]);
        const product = computed(() => useProductsData().getProducts.find(e => e.id == Number(props.id)))
        const url = import.meta.env.VITE_API_URL;
        const excellFileNode = ref();
        const drag = ref(false);
        const sortChanged = ref(false);
        const productSettingsVisible = ref(false);
        const idInSettings = ref<number | false>();
        const parameterUpdating = ref(false);
        const olListModalOpen = ref(false);
        const olList = ref<ITkpVariant[]>();
        const olIsLoading = ref(false);
        const excellDownloading = ref(false);
        const excellUploading = ref(false);
        const exporting = ref(false);
        const importing = ref(false);
        const tablesModalIsOpen = ref(false);
        const productTablesList = ref<string[]>([]);
        const createParamModalVisible = ref(false);
        const productStatistics = ref<Record<string, any>[]>([]);

        const downloadExcell = async () => {
            try {
                excellDownloading.value = true;
                const response = await Api.post(`tables/download_xlsx?product_id=${props.id}`, undefined, { responseType: 'blob' }, undefined, true);
                const contentDisposition = response.headers['content-disposition'];
                const filename = contentDisposition?.split('filename=')[1].replaceAll('"', '');
                download(response.data, String(filename));
            }
            catch (error) { console.error(error) }
            finally { excellDownloading.value = false }
        }

        const handleExcellUpload = async (file: File) => {
            excellUploading.value = true;
            const body = new FormData();
            body.append('file', file);
            try {
                await Api.post(`tables/upload_xlsx?product_id=${props.id}`, body)
            }
            catch (error) {
                console.error('excellUpload', error)
            }
            finally {
                excellUploading.value = false;
                getParams();
            }
        }

        const exportProduct = async () => {
            exporting.value = true;
            try {
                const blob = await Api.get(`products/${props.id}/export`, { responseType: 'blob' });
                const filename = `product_${props.id}.zip`;
                download(blob, filename);
            }
            catch (error) { console.error('exportProduct', error) }
            finally { exporting.value = false }
        }

        const handleImportFile = async (file: File) => {
            if (!file) return;
            const fd = new FormData();
            fd.append('archive', file);
            importing.value = true;
            try {
                const data = await Api.post('products/import', fd);
                if (data && data.id) {
                    toast.success(`Продукт импортирован (id=${data.id})`);
                    window.location.href = `/admin/product/${data.id}`;
                }
            }
            catch (error) {
                console.error('importProduct', error);
                toast.error('Ошибка импорта');
            }
            finally {
                importing.value = false;
            }
        }

        const getParams = async () => {
            try {
                const products: IParameter[] = await Api.get(`parameters/by_product/${props.id}`)
                if (!products || 'detail' in products) { productTableType.value = [] }
                else {
                    productTableType.value = (products as IParameter[]).sort((a, b) => Number(a['sort']) - Number(b['sort']));
                    productTablesList.value = Array.from(new Set(products.map(e => e.table_name)));
                }
            }
            catch {
                productTableType.value = []
            }
        }

        const loadProductStatistics = async () => {
            if (!props.id || props.id === 'null') {
                productStatistics.value = []
                return
            }
            try {
                productStatistics.value = await Api.get(`selection_statistic/selection?product_id=${props.id}`) || []
            } catch {
                productStatistics.value = []
            }
        }

        const safeProductId = computed(() => {
            const id = Number(props.id)
            return Number.isFinite(id) ? id : null
        })

        onMounted(async () => {
            getParams();
            getOlList();
            loadProductStatistics();
        })

        const getOlList = async () => {
            if (props.id)
                olList.value = await getTkpVariants(props.id) || []
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
            sortChanged.value = true;
            drag.value = true;
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
            sortChanged.value = false;
            const newBody = productTableType.value.map((e, index) => {
                e.sort = index + 1;
                return e
            })
            await Api.put(`/parameters/sort/${props.id}`, newBody)
        }

        const changeSettings = (id: number) => {
            productSettingsVisible.value = true;
            idInSettings.value = id;
        }

        const updateParameter = async (id: number, parameter: Record<string, unknown>) => {
            parameterUpdating.value = true;
            try {
                await Api.put(`parameters/${id}`, parameter)
            }
            finally {
                getParams();
                parameterUpdating.value = false
                productSettingsVisible.value = false
            }
        }

        const removeOl = async (id: number) => {
            try {
                await Api.delete(`tkp_generation/delete/${id}`)
                await getOlList();
            } catch (error) {
                console.error(error)
            }
        }

        const uploadOl = async (fileFormData: FormData) => {
            olIsLoading.value = true;
            try {
                const data = await Api.post('tkp_generation/add', fileFormData);
                if (data) {
                    toast.success('ТКП успешно загружено')
                }
                await getOlList();
            } catch (error) {
                console.error(error)
            } finally {
                olIsLoading.value = false;
            }
        }

        const deleteTableFromProduct = async (tableName: string) => {
            try {
                await Api.delete(`tables/${props.id}/${tableName}`)
                await getParams();
            } catch (error) {
                console.error(error)
            }
        }

        return {
            url,
            productTableType,
            createParamModalVisible,
            productStatistics,
            loadProductStatistics,
            safeProductId,
            excellFileNode,
            product,
            sortChanged,
            drag,
            productSettingsVisible,
            idInSettings,
            parameterUpdating,
            olList,
            olListModalOpen,
            olIsLoading,
            excellUploading,
            tablesModalIsOpen,
            excellDownloading,
            exporting,
            importing,
            handleImportFile,
            productTablesList,
            actionButtons: [{ name: 'tkp', title: 'Загруженные ТКП' }, { name: 'tables', title: 'Загруженные таблицы' }],
            removeOl,
            downloadExcell,
            sendNewSort,
            handleExcellUpload,
            exportProduct,
            deleteParam,
            startDrag,
            onOver,
            onLeave,
            onDrop,
            onStart,
            onEnd,
            changeSettings,
            updateParameter,
            getTkpVariants,
            uploadOl,
            deleteTableFromProduct
        }
    }
});
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
