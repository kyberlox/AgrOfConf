<template>
<div class="rounded-[16px] p-[16px] gap-[8px] flex flex-col border border-[#EAECEF] bg-[#FDFDFD]">
    <div v-if="isLogin"
         class="rounded-[8px]  w-full p-[12px] flex flex-row justify-between items-center border border-[#EAECEF] hover:border-orange-500 transition duration-300 cursor-pointer w-fit"
         :class="isSidebarRolled ? 'w-fit' : 'min-w-[283px]'"
         @click="layoutStore.toggleSidebar">
        <div class="flex flex-row gap-[12px] items-center max-w-fit w-full">
            <!-- <span>{{ userAvatar }}</span> -->
            <div class="w-[40px] h-[40px] min-h-[40px] rounded-[8px] bg-cover"
                 :style="{ backgroundImage: `url('${userAvatar}')` }">
            </div>
            <div class="flex flex-col gap-[4px] transition-all duration-300 ease-in-out"
                 v-if="!isSidebarRolled"
                 :class="isSidebarRolled
                    ? 'opacity-0 -translate-x-0 max-w-0 overflow-hidden '
                    : 'opacity-100 translate-x-0 max-w-[200px] max-w-fit!'">
                <span class="text-[13px] text-(--text-primary) whitespace-nowrap">
                    {{ userFio?.split(' ')[0] }}
                </span>
                <span class="text-[11px] text-(--text-secondary) whitespace-nowrap">
                    {{ user.work_position }}
                </span>
            </div>
        </div>
        <ArrowLeft v-if="!isSidebarRolled"
                   class="min-w-[5px] max-w-[5px] text-(--icon-secondary)" />
    </div>
    <div v-if="isLogin"
         v-for="(link, index) in sidebarLinks.filter(e => checkRights(e.name as string, requestsData))"
         :key="'side' + index"
         class="text-(--icon-secondary) hover:text-(--icon-primary) p-[12px] cursor-pointer rounded-[8px] transition-all duration-300 w-fit"
         :class="[{ 'bg-[#FFF2E5] text-(--icon-primary)!': activeTab == link.route }, { 'w-full': !isSidebarRolled }]"
         @mousedown="mouseTab = link.name"
         @mouseup="mouseTab = ''">
        <div class="flex flex-row w-full items-center border rounded-[8px] px-[8px] py-[6px] border-transparent hover:border-[#F36E3C]  transition-all duration-300"
             :class="{ 'bg-[#FFF2E5] border-transparent!': mouseTab == link.name }"
             @click.stop.prevent="handleRoute(link.route)">
            <div>
                <Component :is="link.icon"
                           class="w-[24px] h-[24px]" />
            </div>
            <div class="ml-[8px] text-[14px] font-[500]"
                 :class="{ 'hidden': isSidebarRolled }">
                {{ link.title }}
            </div>
            <div class="ml-auto"
                 v-if="!link.route"
                 :class="{ 'hidden': isSidebarRolled }">
                <ArrowDown />
            </div>
        </div>
        <LeftSidebarFilters :class="{ 'hidden': isSidebarRolled }"
                            v-if="(link.name == 'myRequests' || link.name == 'koRequests') && activeTab == link.route"
                            :tabs="tabsCheck(link)"
                            :link="link.route" />
    </div>
    <!-- Кнопка выйти -->
    <BaseButton :propsClass="'button-secondary'"
                @clicked="handleLoginClick">
        <div class="flex flex-row items-center justify-center "
             :class="{ 'min-w-[283px]': !isSidebarRolled }">
            <LogoutIcon />
            <span :class="{ 'hidden': isSidebarRolled }">
                {{ isLogin ? 'Выйти' : 'Войти' }}
            </span>
        </div>
    </BaseButton>
</div>
</template>

<script lang='ts'>
import { defineComponent, ref, computed, watch } from 'vue';
import ArrowLeft from '@/assets/icons/ArrowLeft.svg?component';
import ArrowDown from '@/assets/icons/ArrowDown.svg?component';
import LogoutIcon from '@/assets/icons/logout.svg?component';
import { BaseButton } from 'beans-ui-kit';
import { sidebarLinks } from '@/assets/static/leftSidebarNav';
import { requestsData } from '@/assets/static/requestsData.ts';
import type { IRequestsData } from '@/assets/interfaces/IUserData';
import LeftSidebarFilters from './LeftSidebarFilters.vue';
import { useUserStore } from '@/stores/user.ts';
import { useRouter, useRoute } from 'vue-router';
import { useLayoutStore } from '@/stores/layout.ts';

export default defineComponent({
    components: {
        ArrowLeft,
        ArrowDown,
        LogoutIcon,
        LeftSidebarFilters,
        BaseButton,
    },
    props: {},
    setup() {
        const router = useRouter();
        const route = useRoute();
        const activeTab = ref();
        const isLogin = computed(() => useUserStore().getIsLogin);
        const layoutStore = useLayoutStore();

        watch((route), () => {
            if (route.name) activeTab.value = route.name
        })

        const mouseTab = ref('');

        const checkRights = (route: string | 'myRequests' | 'koRequests' | 'profileSettings' | 'admin', data: IRequestsData) => {
            if (route == 'admin' && !data.isAdmin) return false
            else if (route == 'koRequests' && !('requestsData' in data)) return false
            else
                return true
        }

        const handleRoute = (route: string) => {
            // if (route == 'user' || route == 'myRequests') {
            //     router.push({ name: route, params: { id: 2366 } })
            // }
            // else
            //     router.push({ name: route })
            if (route == 'user') {
                router.push({ name: route, params: { id: 2366 } })
            } else if (route == 'admin') {
                router.push({ name: route })
            } else
                router.push({ name: route })
            activeTab.value = route
        }

        const handleLoginClick = () => {
            isLogin.value ? useUserStore().setLogin(false) : router.push({ name: 'login' })
        }

        return {
            requestsData,
            sidebarLinks,
            activeTab,
            mouseTab,
            isLogin,
            tabsCheck: (link: { name: string }) => link.name == 'myRequests' ?
                [{ title: 'Статус', name: 'status' }] :
                [{ title: 'КО', name: 'ko' }, { title: 'Пользователь', name: 'user' }, { title: 'Статус', name: 'status' }],
            checkRights,
            userId: computed(() => useUserStore().getId),
            handleRoute,
            user: computed(() => useUserStore().getUser),
            userFio: computed(() => useUserStore().getFio),
            userAvatar: computed(() => useUserStore().getAvatar),
            layoutStore,
            isSidebarRolled: computed(() => useLayoutStore().getIsSidebarRolled),
            handleLoginClick
        }
    }
});
</script>