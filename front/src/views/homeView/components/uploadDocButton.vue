<template>
<div class="dropzone-container p-[20px] w-[480px] max-w-full border border-(--color-information-orange-200) hover:bg-(--color-information-orange-200) transition-all duration-300 cursor-pointer border-dotted flex flex-col gap-[4px] rounded-[12px] text-center"
     ref="dropzoneElement">
    <form class="dropzone"
          id="my-awesome-dropzone">
        <div class="dz-message"
             v-if="!uploadedFileName"
             data-dz-message>
            <span class="text-[16px] font-semibold text-(--color-information-orange-800)">
                Распознать ОЛ
            </span>
            <span class="text-[13px] font-normal text-(--text-text-secondary) block mt-1">
                Фото или PDF до 20мб
            </span>
            <span class="text-[12px] text-(--text-text-tertiary) block mt-2">
                Перетащите файл сюда или нажмите для выбора
            </span>
        </div>
        <div v-else
             class="text-[16px] text-(--text-text-tertiary) block mt-2">
            {{ uploadedFileName }}
        </div>
    </form>
    <div class="dz-preview hidden"></div>
</div>
</template>

<script lang='ts'>
import { defineComponent, ref, onMounted, onUnmounted } from 'vue';
import Dropzone from "dropzone";
import "dropzone/dist/dropzone.css";
import { useRouter } from 'vue-router';
import { neuroOlData } from '@/stores/neuroOl';

export default defineComponent({
    name: 'UploadDocButton',
    setup() {
        const dropzoneElement = ref<HTMLElement | null>(null);
        let dropzoneInstance: Dropzone | null = null;
        const uploadedFileName = ref('');

        onMounted(() => {
            if (!dropzoneElement.value) return;
            Dropzone.autoDiscover = false;
            dropzoneInstance = new Dropzone(dropzoneElement.value.querySelector('form') as HTMLElement, {
                url: "http://agrofconf.emk.org.ru/api/AI/upload_OL",
                paramName: "file",
                maxFilesize: 20,
                maxFiles: 1,
                acceptedFiles: "image/*,.pdf",
                dictDefaultMessage: "",
                dictFallbackMessage: "Ваш браузер не поддерживает загрузку файлов перетаскиванием.",
                dictFileTooBig: "Файл слишком большой ({{filesize}}MB). Максимальный размер: {{maxFilesize}}MB.",
                dictInvalidFileType: "Недопустимый тип файла. Разрешены только изображения и PDF.",
                dictResponseError: "Ошибка сервера (код {{statusCode}}).",
                dictCancelUpload: "Отменить загрузку",
                dictUploadCanceled: "Загрузка отменена.",
                dictCancelUploadConfirmation: "Вы уверены, что хотите отменить загрузку?",
                dictRemoveFile: "Удалить файл",
                dictMaxFilesExceeded: "Можно загрузить только один файл.",
                addRemoveLinks: true,
                createImageThumbnails: true,
                thumbnailWidth: 120,
                thumbnailHeight: 120,
                previewsContainer: dropzoneElement.value.querySelector('.dz-preview') as HTMLElement,
                init: function () {
                    this.on("addedfile", (file) => {
                        console.log("Файл добавлен:", file);
                        uploadedFileName.value = file.name;
                    });
                    this.on("success", (file, response) => {
                        console.log("Файл успешно загружен:", file, response);
                        useRouter().push({ name: 'configurator', params: { id: 1 } })
                        neuroOlData().setData(response)
                    });
                    this.on("error", (file, errorMessage) => {
                        console.error("Ошибка загрузки:", errorMessage);
                    });
                    this.on("removedfile", (file) => {
                        console.log("Файл удален:", file);
                    });
                }
            });
        });

        onUnmounted(() => {
            if (dropzoneInstance) {
                dropzoneInstance.destroy();
            }
        });

        return {
            uploadedFileName,
            dropzoneElement
        };
    }
});
</script>

<style>
.dropzone {
  border: none !important;
  background: transparent !important;
  min-height: auto !important;
  padding: 0 !important;
}

.dropzone .dz-message {
  margin: 0 !important;
}

.dropzone .dz-preview {
  margin-top: 16px;
}

.dropzone .dz-preview .dz-image {
  border-radius: 8px;
}

.dropzone .dz-preview .dz-details {
  padding: 8px;
}

.dropzone .dz-preview .dz-success-mark,
.dropzone .dz-preview .dz-error-mark {
  display: none;
}

.dropzone .dz-preview .dz-error-message {
  top: 140px;
}

.dropzone .dz-preview .dz-remove {
  font-size: 14px;
  color: var(--color-information-orange-800);
  text-decoration: underline;
}

.dropzone .dz-preview .dz-remove:hover {
  color: var(--color-information-orange-600);
}
</style>