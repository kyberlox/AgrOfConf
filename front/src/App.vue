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
import { defineComponent, onMounted, computed } from 'vue';
import VHeader from './components/layout/VHeader.vue';
import LeftSidebar from './components/layout/LeftSidebar.vue';
import { type IUser } from './assets/interfaces/IUser.ts';
import Api from './utils/Api.ts';
import { useUserStore } from './stores/user.ts';

export default defineComponent({
  components: {
    VHeader,
    LeftSidebar
  },
  props: {},
  setup() {
    const userStore = useUserStore();

    const authorize = async () => {
      try {
        const user: IUser = await Api.get('auth/user_id_by_session_id')
        if (user) {
          try {
            const userData: IUser = await Api.get(`users/find_by/${user}`)
            userStore.setUser(userData)
          } catch (error) {
            console.error(error)
          }
        }
      } catch (error) {
        console.error(error)
      }
    }

    onMounted(async () => {
      await authorize()
    })

    return {
      isLogin: computed(() => userStore.getIsLogin),
    }
  }
});
</script>