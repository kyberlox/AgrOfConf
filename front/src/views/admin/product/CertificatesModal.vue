<template>
  <SlotModal v-if="isOpen" @closeModal="$emit('closeModal')">
    <div class="flex flex-col p-[15px]">
      <h4>Список сертификатов / документов</h4>
      <div class="flex flex-col mt-[15px] gap-[15px] max-h-[700px] overflow-auto">
        <div
          class="border border-gray-200 px-[15px] py-[5px] h-[50px] rounded-[16px] bg-blue-50 flex flex-row justify-between items-center gap-[15px]"
          v-for="file in filesList" :key="file.id">
          <a :href="apiUrl + file.file_url.replace('/api', '')" target="_blank"
            class="font-semibold text-blue-700 hover:text-blue-500 truncate">
            {{ file.name }}
          </a>
          <div class="flex flex-row items-center gap-[12px] flex-nowrap shrink-0">
            <span class="text-[12px] text-gray-500">Срок действия: {{ file.date_to }}</span>
            <div class="text-[12px] underline text-red-600 cursor-pointer hover:text-red-400"
              @click="$emit('removeFile', file.id)">
              Удалить
            </div>
          </div>
        </div>
      </div>
      <div class="mt-[15px] flex flex-col gap-[15px] border border-gray-200 rounded-[16px] p-[20px] max-w-[500px]">
        <span>Для добавления нового документа - заполните название, срок действия и выберите
          файл</span>
        <BaseInput v-for="field in certificateFields" :key="field" :inputSettings="initInputProps(field)"
          @value-changed="(value) => updateField(field, value)" />
        <UploadFileArea :disabled="!fileName || !fileDateTo" :formats="'.pdf,.jpg,.jpeg,.png,.docx,.xlsx'"
          @ready-to-upload-file="uploadCertToProduct">
          Добавить
        </UploadFileArea>
      </div>
    </div>
  </SlotModal>
</template>

<script lang="ts">
import { defineComponent, ref, type PropType } from 'vue'
import UploadFileArea from '@/components/layout/UploadFileArea.vue'
import { type IProductFile } from '@/assets/interfaces/IProductFile.ts'
import { BaseInput } from 'beans-ui-kit'
import SlotModal from '@/components/layout/SlotModal.vue'

const certificateFields = ['name', 'date_to'] as const

export default defineComponent({
  components: {
    UploadFileArea,
    BaseInput,
    SlotModal,
  },
  props: {
    filesList: {
      type: Array as PropType<IProductFile[]>,
    },
    id: {
      type: String,
      required: true,
    },
    isLoading: {
      type: Boolean,
      default: false,
    },
    isOpen: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['updateFilesList', 'removeFile', 'closeModal'],
  setup(props, { emit }) {
    const fileName = ref<string>()
    const fileDateTo = ref<string>()
    const apiUrl = import.meta.env.VITE_API_URL

    const uploadCertToProduct = (formDataFile: FormData) => {
      const file = formDataFile.get('file')
      if (!(file instanceof Blob) || !fileName.value || !fileDateTo.value) return
      const uploadData = new FormData()
      uploadData.append('image', file)
      uploadData.append('product_id', props.id)
      uploadData.append('name', fileName.value)
      uploadData.append('date_to', fileDateTo.value)
      emit('updateFilesList', uploadData)
      fileName.value = ''
      fileDateTo.value = ''
    }

    const initInputProps = (field: 'name' | 'date_to') => {
      return {
        class: 'input-admin',
        placeholder:
          field == 'date_to' ? 'Введите срок действия (ДД.ММ.ГГГГ)' : 'Введите название документа',
        disabled: props.isLoading,
        value: field == 'date_to' ? fileDateTo.value : fileName.value,
      }
    }

    const updateField = (field: 'name' | 'date_to', value: string) => {
      if (field === 'name') fileName.value = value
      else fileDateTo.value = value
    }

    return {
      apiUrl,
      fileName,
      fileDateTo,
      certificateFields,
      initInputProps,
      updateField,
      uploadCertToProduct,
    }
  },
})
</script>
