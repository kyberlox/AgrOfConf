<template>
    <div>
        <div class="flex flex-row justify-start gap-[25px] flex-wrap">
            <div class="max-w-full lg:max-w-[40%] p-4 bg-blue-50 border border-blue-200 rounded-lg shadow-sm">
                <div class="text-lg text-blue-800 font-medium mb-2 grow">Информация о редактировании</div>
                <div class="text-md text-gray-700">
                    Для изменения логики подбора по табличным параметрам необходимо отредактировать исходный excel
                    файл, сперва скачав его, отредактировав и затем загрузив по кнопкам в блоке Excel. Добавить или
                    отредактировать формульные параметры можно по нажатию на блок или кнопку «Создать параметр».
                </div>
            </div>

            <div class="flex justify-start gap-2">
                <div
                    class="flex flex-row flex-wrap md:flex-nowrap gap-2 items-center border border-green-300 bg-green-100 rounded-md p-4">
                    <div class="text-lg w-full">Excel</div>
                    <BaseButton
                        :buttonSettings="{ class: 'button-primary', disabled: excelDownloading }"
                        @click="$emit('downloadExcel')">
                        <Loader v-if="excelDownloading" class="button-primary__loader" />
                        <span v-else>Скачать</span>
                    </BaseButton>
                    <VInputFile
                        :buttonClass="'button-primary'"
                        :needFileNameInTitle="false"
                        :isLoading="excelUploading"
                        @fileUpload="(file) => $emit('uploadExcel', file)" />
                </div>
            </div>

            <div class="flex justify-start gap-2">
                <div
                    class="flex flex-row flex-wrap md:flex-nowrap gap-2 items-center border border-indigo-300 bg-indigo-100 rounded-md p-4">
                    <div class="text-lg w-full">Перенос конфигурации</div>
                    <BaseButton
                        :buttonSettings="{ class: 'button-primary', disabled: exporting }"
                        @clicked="$emit('exportProduct')">
                        <Loader v-if="exporting" class="button-primary__loader" />
                        <span v-else>Экспорт</span>
                    </BaseButton>
                    <VInputFile
                        :buttonClass="'button-primary'"
                        :needFileNameInTitle="false"
                        :fileName="'Импорт'"
                        :isLoading="importing"
                        @fileUpload="(file) => $emit('importProduct', file)" />
                </div>
            </div>

            <div class="w-fit m-auto">
                <Transition name="fade-btn">
                    <BaseButton
                        v-if="sortChanged"
                        :buttonSettings="{ class: 'button-primary' }"
                        @clicked="$emit('saveSort')">
                        Принять сортировку
                    </BaseButton>
                </Transition>
            </div>
        </div>

        <div class="flex flex-row items-center justify-start gap-[15px]">
            <div v-for="item in actionButtons" :key="item.name" class="mt-[20px] max-w-[250px] w-[250px]">
                <BaseButton :buttonSettings="{ class: 'button-secondary' }" @clicked="$emit('openAction', item.name)">
                    {{ item.title }}
                </BaseButton>
            </div>
            <div class="mt-[20px] max-w-[250px] w-[250px]">
                <BaseButton :buttonSettings="{ class: 'button-primary' }" @clicked="$emit('createParameter')">
                    Создать параметр
                </BaseButton>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { BaseButton } from "beans-ui-kit";
import Loader from "@/components/layout/Loader.vue";
import VInputFile from "@/components/layout/VInputFile.vue";

const actionButtons = [
    { name: "tkp", title: "Загруженные ТКП" },
    { name: "tables", title: "Загруженные таблицы" },
    { name: "files", title: "Сертификаты" },
] as const;

export default defineComponent({
    components: {
        BaseButton,
        Loader,
        VInputFile,
    },
    props: {
        excelDownloading: { type: Boolean, required: true },
        excelUploading: { type: Boolean, required: true },
        exporting: { type: Boolean, required: true },
        importing: { type: Boolean, required: true },
        sortChanged: { type: Boolean, required: true },
    },
    emits: [
        "downloadExcel",
        "uploadExcel",
        "exportProduct",
        "importProduct",
        "saveSort",
        "openAction",
        "createParameter",
    ],
    setup() {
        return { actionButtons };
    },
});
</script>

<style>
.fade-btn-enter-active,
.fade-btn-leave-active {
    transition: opacity 0.3s ease;
}

.fade-btn-enter-from,
.fade-btn-leave-to {
    opacity: 0;
}
</style>
