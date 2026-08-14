<template>
<div class="grid grid-rows-[auto_1fr] h-[100vh] bg-[#F6F7F9]">
  <div class="p-[24px] bg-[#F6F7F9] flex flex-row gap-[32px]">
    <LeftSidebar />
    <div class="max-w-[calc(100%-114px)] ml-auto grow">
      <RouterView />
    </div>
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
import LogoIcon from '@/assets/img/logo.svg?component';

export default defineComponent({
  components: {
    VHeader,
    LeftSidebar,
    LogoIcon
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