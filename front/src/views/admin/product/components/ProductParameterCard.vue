<template>
  <li
    class="flex flex-col py-[20px] px-[15px] border border-green-200 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 bg-green-50 relative cursor-move"
    :class="{ 'bg-blue-50! border-blue-200!': parameter.type === 'Formula' }">
    <div class="text-lg pr-[25px] font-medium text-gray-800 mb-2 wrap-break-word">
      <span>{{ parameter.name }}</span>
      <span v-if="parameter.special"
        class="ml-[8px] align-middle text-[11px] px-[8px] py-[2px] rounded-full bg-orange-100 text-orange-700 border border-orange-200">
        специальный
      </span>
    </div>
    <div class="text-sm text-gray-600 mb-3 wrap-break-word">
      {{ parameter.description }}
    </div>
    <div class="text-xs text-gray-500 wrap-break-word">
      Из таблицы: {{ parameter.table_name }}
    </div>
    <button type="button"
      class="w-[24px] h-[24px] p-[5px] rounded-lg bg-mist-100 absolute top-[15px] right-[40px] cursor-pointer hover:bg-mist-300 text-[var(--icon-color-secondary)] hover:text-[var(--icon-color-primary)]"
      title="Удалить параметр" @click.stop="$emit('delete', parameter.id)">
      <CloseIcon class="text-red-500" />
    </button>
    <button type="button"
      class="w-[24px] h-[24px] p-[5px] rounded-lg bg-mist-100 absolute top-[15px] right-[15px] cursor-pointer hover:bg-mist-300 text-[var(--icon-color-secondary)] hover:text-[var(--icon-color-primary)]"
      title="Изменить параметр" @click.stop="$emit('edit', parameter.id)">
      <SettingsIcon />
    </button>
  </li>
</template>

<script setup lang="ts">
import type { IParameter } from "@/assets/interfaces/IParameter";
import CloseIcon from "@/assets/icons/Cross.svg?component";
import SettingsIcon from "@/assets/icons/Settings.svg?component";

defineProps<{
  parameter: IParameter;
}>();

defineEmits<{
  delete: [id: number];
  edit: [id: number];
}>();
</script>
