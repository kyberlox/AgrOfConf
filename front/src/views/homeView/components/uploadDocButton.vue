<template>
<div class="dropzone-container p-[20px] w-[480px] max-w-full border border-(--color-information-orange-200) hover:bg-(--color-information-orange-200) transition-all duration-300 cursor-pointer border-dotted flex flex-col gap-[4px] rounded-[12px] text-center"
     :class="{ 'bg-(--color-information-green-50) hover:bg-(--color-information-green-150)!': type == 'inConfig' }"
     ref="dropzoneElement"
     @click="handleContainerClick">
    <form class="dropzone cursor-pointer!"
          id="my-awesome-dropzone">
        <div class="dz-message"
             v-if="!uploadedFileName && type == 'outer'"
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
        <div class="flex flex-row items-center justify-between"
             v-else-if="type == 'inConfig'">
            <div class="flex flex-col gap-[4px] text-left">
                <span class="text-[16px] font-semibold text-(--text-text-primary)">
                    Поля Распознаны
                </span>
                <span class="text-[13px] font-normal text-(--text-text-secondary) block">
                    Перепроверьте на всякий случай
                </span>
            </div>
            <span class="text-[16px] text-(--color-information-orange-800) block ">
                Загрузить другой
            </span>
        </div>
        <div v-else
             class="text-[16px] text-(--text-text-tertiary) block">
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
import { useNeuroOlData } from '@/stores/neuroOl';

export default defineComponent({
    name: 'UploadDocButton',
    props: {
        type: {
            type: String,
            default: 'outer'
        }
    },
    setup() {
        const dropzoneElement = ref<HTMLElement | null>(null);
        let dropzoneInstance: Dropzone | null = null;
        const uploadedFileName = ref('');
        const router = useRouter();

        const handleContainerClick = (event: MouseEvent) => {
            // Предотвращаем двойное срабатывание при клике на форму
            if ((event.target as HTMLElement).closest('form')) {
                return;
            }

            // Если есть экземпляр Dropzone, открываем диалог выбора файла
            if (dropzoneInstance) {
                dropzoneInstance.hiddenFileInput?.click();
            }
        };

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
                        useNeuroOlData().setData(response as Object)
                        console.log(useNeuroOlData().getOlInfo);

                        router.push({ name: 'configurator', params: { id: 1 } })
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
            dropzoneElement,
            handleContainerClick
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
  cursor: pointer !important;
}

.dropzone.dz-clickable *{
  cursor: pointer !important;
}

.dropzone-container{
  cursor: pointer !important;
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
  /* top: 140px; */
}


.dropzone .dz-preview .dz-remove {
  font-size: 14px;
  color: var(--color-information-orange-800);
  text-decoration: underline;
}

.dropzone .dz-preview .dz-remove:hover {
  color: var(--color-information-orange-600);
}

.dz-default.dz-message {
  display: none !important;
}
</style>