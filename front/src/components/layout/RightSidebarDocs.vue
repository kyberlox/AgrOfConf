<template>
<div class="sidebar-block p-[24px]">
    <div class="text-13 text-[#343B4C] font-semibold"
         v-html="displayTitle">
    </div>
    <a :href="apiUrl + doc.file_url"
       target="_blank"
       class="mt-[8px] relative grid grid-cols-[1fr] items-center gap-[6px] border-b border-b-(--color-information-gray-100) py-[12px]"
       :class="'sidebar-block__date__wrapper--' + doc.status"
       v-for="doc in formattedDocs?.filter((doc) => type == 'actual' ? doc.status !== 'outdated' : doc.status === 'outdated')"
       :key="doc.id">
        <div
             class="flex text-sm truncate flex-row items-center flex-nowrap  justify-between group cursor-pointer hover:text-gray-600">
            <span class="mr-[10px]">
                <FileIcon />
            </span>
            <span class="truncate block mr-[12px] font-normal! grow relative peer">
                {{ doc.name }}
            </span>
            <div
                 class="absolute max-w-full top-[50px] z-10 whitespace-normal invisible bg-white text-black text-sm shadow-[0_0_8px_0] rgba(180, 188, 200, 0.5) px-[16px] py-[8px] rounded-[5px] group-hover:visible!">
                {{ doc.name }}
            </div>
            <div
                 class="p-[4px] bg-(--color-information-gray-50) group-hover:bg-(--color-information-gray-100) duration-100 rounded-md">
                <DownloadIcon />
            </div>
        </div>
        <div class="ml-auto text-[12px]">
            Срок действия:
            <span class="sidebar-block__date">{{ doc.date_to }}</span>
        </div>
    </a>
    <BaseButton class="mt-[12px] flex flex-row items-center"
                propsClass="button-secondary"
                @clicked="$emit('downloadZip')">
        <DownloadIcon class="w-[24px] h-[24px]" />
        <span>Скачать все</span>
    </BaseButton>
</div>
</template>

<script lang="ts">
import { defineComponent, type PropType, ref, onMounted, computed } from 'vue';
import { checkDateStatus } from '@/utils/checkDateStatus';
import DownloadIcon from '@/assets/icons/DownloadIcon.svg?component';
import FileIcon from '@/assets/icons/FileIcon.svg?component';
import { BaseButton } from 'beans-ui-kit';

export default defineComponent({
    emits: ['downloadZip'],
    props: {
        docs: {
            type: Object as PropType<{ id: number, name: string, date_to: string, file_url: string }[]>,
            required: true
        },
        type: {
            type: String as PropType<"actual" | "outdated">,
            required: true
        }
    },
    components: {
        BaseButton,
        DownloadIcon,
        FileIcon
    },
    setup(props) {
        const apiUrl = import.meta.env.VITE_API_URL;
        const formattedDocs = ref<{ id: number, name: string, date_to: string, status: string, file_url: string }[]>();

        const formatDocs = () => {
            formattedDocs.value = props.docs.map((doc) => {
                return {
                    ...doc,
                    status: checkDateStatus(doc.date_to)
                }
            })
        }

        onMounted(() => {
            formatDocs();
        })


        return {
            formattedDocs,
            apiUrl,
            checkDateStatus,
            displayTitle: computed(() => props.type == 'actual' ?
                `<span class="text-green-500">Актуальные</span> документы` :
                `<span class="text-red-500">Истекшие</span> документы`),
        }
    }
})
</script>