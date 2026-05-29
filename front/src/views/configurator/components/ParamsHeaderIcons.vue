<template>
<div class="flex flex-row w-fit justify-between grow items-center">
    <InfoCircle class="info-circle w-[15px]"
                @click="$emit('descriptionClicked')"
                v-if="needDescription" />
    <RequiredIcon class="ml-auto"
                  v-if="needReq" />
</div>
</template>
<script lang='ts'>
import { defineComponent } from 'vue';
import InfoCircle from '@/assets/icons/InfoCircle.svg?component'
import RequiredIcon from '@/assets/icons/RequiredIcon.svg?component'

export default defineComponent({
    components: {
        InfoCircle,
        RequiredIcon,
    },
    props: {
        needReq: {
            type: Boolean,
            default: false
        },
        needDescription: {
            type: Boolean,
            default: false
        }
    },
    setup() {
        return {}
    }
});
</script>