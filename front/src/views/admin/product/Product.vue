<template>
    <div class="min-h-[86vh] bg-white rounded-lg w-full p-[16px]">
        <ProductAdminHeader
            :excelDownloading="excelDownloading"
            :excelUploading="excelUploading"
            :exporting="exporting"
            :importing="importing"
            :sortChanged="sortChanged"
            @downloadExcel="downloadExcel"
            @uploadExcel="handleExcelUpload"
            @exportProduct="exportProduct"
            @importProduct="handleImportFile"
            @saveSort="sendNewSort"
            @openAction="handleActionButton"
            @createParameter="createParamModalVisible = true" />

        <ProductStatisticsPanel :statistics="productStatistics" />

        <div class="mt-[20px]">
            <BlocksManager v-if="safeProductId !== null" :productId="safeProductId" @changed="getParams" />
        </div>

        <ProductParametersPanel
            v-model="productTableType"
            @sortStart="onStart"
            @sortEnd="onEnd"
            @deleteParameter="deleteParam"
            @editParameter="changeSettings" />

        <ParameterSettings
            v-if="productSettingsVisible && selectedParameter"
            :parameter="selectedParameter"
            :disabled="parameterUpdating"
            @updateParameter="(id, parameter) => updateParameter(id, parameter)"
            @closeModal="closeParameterSettings" />

        <UploadedOl
            v-if="id"
            :id="id"
            :isOpen="olListModalOpen"
            :olList="olList"
            :olIsLoading="olIsLoading"
            @closeModal="olListModalOpen = false"
            @updateOlList="uploadOl"
            @removeOl="removeOl" />

        <TablesManageModal
            v-if="tablesModalIsOpen"
            :tables="Array.from(productTablesList)"
            @closeModal="tablesModalIsOpen = false"
            @deleteTable="deleteTableFromProduct" />

        <CertificatesModal
            v-if="id"
            :id="id"
            :isOpen="filesModalIsOpen"
            :filesList="filesList"
            :isLoading="filesIsLoading"
            @closeModal="filesModalIsOpen = false"
            @updateFilesList="uploadFile"
            @removeFile="removeFile" />

        <CreateParameterModal
            v-if="safeProductId !== null"
            :showModal="createParamModalVisible"
            :productId="safeProductId"
            :tables="productTablesList"
            @closeModal="createParamModalVisible = false"
            @created="getParams" />

        <PromptEditBlock :id="Number(id)" :params="productTableType" />
    </div>
</template>
<script lang="ts">
import Api from "@/utils/Api";
import { computed, defineComponent, onMounted, ref } from "vue";
import download from "downloadjs";
import ParameterSettings from "./components/ParameterSettingsModal.vue";
import type { IParameter } from "@/assets/interfaces/IParameter";
import UploadedOl from "./components/UploadedOlModal.vue";
import { getTkpVariants } from "@/utils/getTkpVariants.ts";
import { type ITkpVariant } from "@/assets/interfaces/ITkpVariant.ts";
import { toast } from "vue3-toastify";
import TablesManageModal from "./components/TablesManageModal.vue";
import CreateParameterModal from "./components/CreateParameterModal.vue";
import BlocksManager from "./components/BlocksManager.vue";
import CertificatesModal from "./components/CertificatesModal.vue";
import { getProductFiles } from "@/utils/getProductFiles.ts";
import { type IProductFile } from "@/assets/interfaces/IProductFile.ts";
import PromptEditBlock from "./components/PromptEditBlock.vue";
import ProductAdminHeader from "./components/ProductAdminHeader.vue";
import ProductParametersPanel from "./components/ProductParametersPanel.vue";
import ProductStatisticsPanel from "./components/ProductStatisticsPanel.vue";
import type { ProductStatistic } from "@/assets/interfaces/IProductStatistic.ts";

export default defineComponent({
    components: {
        ParameterSettings,
        UploadedOl,
        TablesManageModal,
        CreateParameterModal,
        BlocksManager,
        CertificatesModal,
        PromptEditBlock,
        ProductAdminHeader,
        ProductParametersPanel,
        ProductStatisticsPanel,
    },
    props: {
        id: {
            type: String,
            required: true,
        },
    },
    setup(props) {
        const productTableType = ref<IParameter[]>([]);
        const sortChanged = ref(false);
        const productSettingsVisible = ref(false);
        const idInSettings = ref<number | false>();
        const parameterUpdating = ref(false);
        const olListModalOpen = ref(false);
        const olList = ref<ITkpVariant[]>([]);
        const olIsLoading = ref(false);
        const excelDownloading = ref(false);
        const excelUploading = ref(false);
        const exporting = ref(false);
        const importing = ref(false);
        const tablesModalIsOpen = ref(false);
        const productTablesList = ref<string[]>([]);
        const createParamModalVisible = ref(false);
        const productStatistics = ref<ProductStatistic[]>([]);
        const filesModalIsOpen = ref(false);
        const filesList = ref<IProductFile[]>([]);
        const filesIsLoading = ref(false);
        const selectedParameter = computed(() =>
            productTableType.value.find((parameter) => parameter.id === idInSettings.value),
        );

        const downloadExcel = async () => {
            try {
                excelDownloading.value = true;
                const response = await Api.post(
                    `tables/download_xlsx?product_id=${props.id}`,
                    undefined,
                    { responseType: "blob" },
                    undefined,
                    true,
                );
                const contentDisposition = response.headers["content-disposition"];
                const filename = contentDisposition?.split("filename=")[1].replaceAll('"', "");
                download(response.data, String(filename));
            } catch (error) {
                console.error(error);
            } finally {
                excelDownloading.value = false;
            }
        };

        const handleExcelUpload = async (file: File) => {
            excelUploading.value = true;
            const body = new FormData();
            body.append("file", file);
            try {
                await Api.post(`tables/upload_xlsx?product_id=${props.id}`, body);
            } catch (error) {
                console.error("excelUpload", error);
            } finally {
                excelUploading.value = false;
                getParams();
            }
        };

        const exportProduct = async () => {
            exporting.value = true;
            try {
                const blob = await Api.get(`products/${props.id}/export`, { responseType: "blob" });
                const filename = `product_${props.id}.zip`;
                download(blob, filename);
            } catch (error) {
                console.error("exportProduct", error);
            } finally {
                exporting.value = false;
            }
        };

        const handleImportFile = async (file: File) => {
            if (!file) return;
            const fd = new FormData();
            fd.append("archive", file);
            importing.value = true;
            try {
                const data = await Api.post("products/import", fd);
                if (data && data.id) {
                    toast.success(`Продукт импортирован (id=${data.id})`);
                    window.location.href = `/admin/product/${data.id}`;
                }
            } catch (error) {
                console.error("importProduct", error);
                toast.error("Ошибка импорта");
            } finally {
                importing.value = false;
            }
        };

        const getParams = async () => {
            try {
                const products = (await Api.get(`parameters/by_product/${props.id}`)) as IParameter[] | undefined;
                if (!Array.isArray(products)) {
                    productTableType.value = [];
                    productTablesList.value = [];
                } else {
                    productTableType.value = [...products].sort((a, b) => a.sort - b.sort);
                    productTablesList.value = Array.from(
                        new Set(products.map((e) => e.table_name).filter((name): name is string => Boolean(name))),
                    );
                }
            } catch {
                productTableType.value = [];
            }
        };

        const loadProductStatistics = async () => {
            if (!props.id || props.id === "null") {
                productStatistics.value = [];
                return;
            }
            try {
                const data = await Api.get(`selection_statistic/selection?product_id=${props.id}`);
                productStatistics.value = Array.isArray(data) ? data : (data?.data ?? []);
            } catch {
                productStatistics.value = [];
            }
        };

        const safeProductId = computed(() => {
            const id = Number(props.id);
            return Number.isFinite(id) ? id : null;
        });

        onMounted(async () => {
            getParams();
            getOlList();
            getFilesList();
            loadProductStatistics();
        });

        const getOlList = async () => {
            if (props.id) olList.value = (await getTkpVariants(props.id)) || [];
        };

        const getFilesList = async () => {
            if (props.id) filesList.value = (await getProductFiles(props.id)) || [];
        };

        const deleteParam = async (id: number) => {
            if (!window.confirm("Удалить параметр? Это действие нельзя отменить.")) return;
            try {
                await Api.delete(`parameters/${id}`);
                await getParams();
            } catch (error) {
                console.error("deleteParam", error);
            }
        };

        const onStart = () => {
            sortChanged.value = true;
        };

        const onEnd = () => {
            // Сохраняем новый порядок параметров сразу после перетаскивания,
            // чтобы он влиял на порядок в подборе.
            sendNewSort();
        };

        const sendNewSort = async () => {
            sortChanged.value = false;
            const newBody = productTableType.value.map((e, index) => {
                e.sort = index + 1;
                return e;
            });
            await Api.put(`/parameters/sort/${props.id}`, newBody);
        };

        const changeSettings = (id: number) => {
            productSettingsVisible.value = true;
            idInSettings.value = id;
        };

        const closeParameterSettings = () => {
            productSettingsVisible.value = false;
            idInSettings.value = false;
        };

        const updateParameter = async (id: number, parameter: Record<string, unknown>) => {
            parameterUpdating.value = true;
            try {
                await Api.put(`parameters/${id}`, parameter);
            } finally {
                getParams();
                parameterUpdating.value = false;
                productSettingsVisible.value = false;
            }
        };

        const removeOl = async (id: number) => {
            try {
                await Api.delete(`tkp_generation/delete/${id}`);
                await getOlList();
            } catch (error) {
                console.error(error);
            }
        };

        const uploadOl = async (fileFormData: FormData) => {
            olIsLoading.value = true;
            try {
                const data = await Api.post("tkp_generation/add", fileFormData);
                if (data) {
                    toast.success("ТКП успешно загружено");
                }
                await getOlList();
            } catch (error) {
                console.error(error);
            } finally {
                olIsLoading.value = false;
            }
        };

        const deleteTableFromProduct = async (tableName: string) => {
            try {
                await Api.delete(`tables/${props.id}/${tableName}`);
                await getParams();
            } catch (error) {
                console.error(error);
            }
        };

        const handleActionButton = (name: string) => {
            if (name == "tkp") olListModalOpen.value = true;
            else if (name == "tables") tablesModalIsOpen.value = true;
            else if (name == "files") filesModalIsOpen.value = true;
        };

        const removeFile = async (id: number) => {
            try {
                await Api.delete(`products/delete_product_file/${id}`);
                await getFilesList();
            } catch (error) {
                console.error(error);
            }
        };

        const uploadFile = async (fileFormData: FormData) => {
            filesIsLoading.value = true;
            try {
                const data = await Api.post("products/upload_product_file", fileFormData);
                if (data) {
                    toast.success("Сертификат успешно загружен");
                }
                await getFilesList();
            } catch (error) {
                console.error(error);
            } finally {
                filesIsLoading.value = false;
            }
        };

        return {
            productTableType,
            createParamModalVisible,
            productStatistics,
            loadProductStatistics,
            getParams,
            safeProductId,
            selectedParameter,
            sortChanged,
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
        };
    },
});
</script>
