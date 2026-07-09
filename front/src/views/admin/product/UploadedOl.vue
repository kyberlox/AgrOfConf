<template>
<div class="flex flex-col p-[15px]">
    <h4>Список загруженных ТКП</h4>
    <div class="flex flex-col mt-[15px] gap-[15px] max-h-[700px] overflow-auto">
        <div class="border border-gray-200 px-[15px] py-[5px] h-[50px] rounded-[16px] bg-blue-50 font-semibold flex flex-row justify-between items-center "
             v-for="ol in olList"
             :key="ol.id">
            <div>
                {{ ol.name }}
            </div>
            <div class="text-[12px] underline text-red-600 cursor-pointer hover:text-red-400"
                 @click="$emit('removeOl', ol.id)">
                Удалить
            </div>
        </div>
    </div>
    <div class="mt-[15px] flex flex-col gap-[15px] border border-gray-200 rounded-[16px] p-[20px] max-w-[500px]">
        <span>Для добавления нового документа - заполните название и нажмите "добавить"</span>
        <BaseInput :propsClass="'input-admin'"
                   :propsPlaceholder="'Введите название документа'"
                   @value-changed="(value) => fileName = value" />
        <UploadFileArea :disabled="!fileName"
                        :uploadFormats="'.xlsx,.docx'"
                        @ready-to-upload-file="uploadOlToProduct">
            Добавить
        </UploadFileArea>
    </div>
</div>
</template>
<script lang='ts'>
import { defineComponent, ref, onMounted, type PropType } from 'vue';
import UploadFileArea from '@/components/layout/UploadFileArea.vue';
import { type ITkpVariant } from '@/assets/interfaces/ITkpVariant.ts';
import { BaseInput } from 'beans-ui-kit';

export default defineComponent({
    components: {
        UploadFileArea,
        BaseInput
    },
    props: {
        olList: {
            type: Array as PropType<ITkpVariant[]>,
        },
        id: {
            type: String,
            required: true
        }
    },
    emits: ['updateOlList', 'removeOl'],
    setup(props, { emit }) {
        const newFileFormData = new FormData();
        const fileName = ref<string>();

        const uploadOlToProduct = (formDataFile: FormData) => {
            newFileFormData.append('file', formDataFile.get('file') as Blob);
            newFileFormData.append('product_id', props.id);
            newFileFormData.append('filename', fileName.value as string);
            emit('updateOlList', newFileFormData)
            fileName.value = '';
        }

        return {
            fileName,
            uploadOlToProduct
        }
    }
});
</script>