<template>
<div class="grid grid-rows-[auto_1fr] h-[100vh]">
  <VHeader />
  <div class="p-[24px] bg-[#F6F7F9] flex flex-row gap-[32px]">
    <LeftSidebar />
    <RouterView />
  </div>
</div>
</template>
<script lang='ts'>
import { defineComponent } from 'vue';
import VHeader from './components/layout/VHeader.vue';
import LeftSidebar from './components/layout/LeftSidebar.vue';

export default defineComponent({
  components: {
    VHeader,
    LeftSidebar
  },
  props: {},
  setup() {
    return {}
  }
});
</script>