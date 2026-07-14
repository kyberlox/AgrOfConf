<template>
<div class="loader">
</div>
<slot></slot>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
    setup() {
        return {

        }
    }
})
</script>

<style scoped>
@keyframes spin {
    0% {
        transform: rotate(0deg);
    }

    100% {
        transform: rotate(360deg);
    }
}

.loader {
    width: 100%;
    height: 100%;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #F36E3C;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}
</style>