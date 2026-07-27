<template>
<div class="loader__wrapper">
    <div class="loader">
    </div>
</div>
<slot></slot>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({ name: 'Loader' })
</script>