<template>
    <div class="flex flex-row gap-[24px]">
        <template v-for="item in [{}]">
            <div class="flex flex-col"></div>
        </template>
    </div>
</template>
<script lang="ts">
import { defineComponent, type PropType } from "vue";
import { type IHistory } from "@/assets/interfaces/IHistory";

export default defineComponent({
    components: {},
    props: {
        requestInfo: {
            type: Object as PropType<IHistory>,
        },
    },
    setup(props) {
        console.log(props);
        return {};
    },
});
</script>
