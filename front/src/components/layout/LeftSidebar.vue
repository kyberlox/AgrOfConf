<template>
<div
     class="rounded-[16px] p-[16px] gap-[8px] flex flex-col border border-[#EAECEF] bg-[#FDFDFD] w-max 2xl:min-w-[283px]">
    <div
         class="rounded-[8px] p-[12px] flex flex-row justify-between items-center border border-[#EAECEF] hover:border-orange-500 transition duration-300 cursor-pointer">
        <div class="flex flex-row gap-[12px] items-center">
            <div class="w-[40px] h-[40px] rounded-[8px] bg-cover"
                 :style="{ backgroundImage: `url(${userData.avatar})` }">
            </div>
            <div class="flex flex-col gap-[4px]">
                <span class="text-[13px] text-(--text-primary)">
                    {{ userData.fio.split(' ')[0] + ' ' + userData.fio.split(' ')[1] }}</span>
                <span class="text-[11px] text-(--text-secondary)">
                    {{ userData.position }}
                </span>
            </div>
        </div>
        <ArrowLeft class="min-w-[5px] max-w-[5px] text-(--icon-secondary)" />
    </div>
    <div v-for="(link, index) in sidebarLinks.filter(e => checkRights(e.name as string, userData))"
         :key="'side' + index"
         class="text-(--icon-secondary) hover:text-(--icon-primary) pl-[20px] pr-[12px] py-[12px] cursor-pointer rounded-[8px] transition-all duration-300"
         :class="[{ 'bg-[#FFF2E5]': activeTab == link.name }]"
         @mousedown="mouseTab = link.name"
         @mouseup="mouseTab = ''">
        <div class="flex flex-row items-center border rounded-[8px] px-[8px] py-[6px] border-transparent hover:border-[#F36E3C]  transition-all duration-300"
             :class="{ 'bg-[#FFF2E5] border-transparent!': mouseTab == link.name }"
             @click.stop.prevent="link.route ? $router.push({ name: link.route }) : activeTab == link.name ? activeTab = '' : activeTab = link.name">
            <div>
                <Component :is="link.icon"
                           class="w-[24px] h-[24px]" />
            </div>
            <div class="ml-[8px] text-[14px] font-[500]">
                {{ link.title }}
            </div>
            <div class="ml-auto"
                 v-if="!link.route">
                <ArrowDown />
            </div>
        </div>
        <LeftSidebarFilters v-if="(link.name == 'myRequests' || link.name == 'koRequests') && activeTab == link.name"
                            :tabs="tabsCheck(link)" />
    </div>
    <BaseButton :propsClass="'button-secondary'">
        <div class="flex flex-row items-center justify-center">
            <LogoutIcon />
            <span>Выйти</span>
        </div>
    </BaseButton>
</div>
</template>

<script lang='ts'>
import { defineComponent, ref } from 'vue';
import ArrowLeft from '@/assets/icons/ArrowLeft.svg?component';
import ArrowDown from '@/assets/icons/ArrowDown.svg?component';
import LogoutIcon from '@/assets/icons/logout.svg?component';
import { BaseButton } from 'beans-ui-kit';
import { sidebarLinks } from '@/assets/static/leftSidebarNav';
import { userData } from '@/assets/static/userData';
import type { IUserData } from '@/assets/interfaces/IUserData';
import LeftSidebarFilters from './LeftSidebarFilters.vue';

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
        const activeTab = ref('');
        const mouseTab = ref('');

        const checkRights = (route: string | 'myRequests' | 'koRequests' | 'profileSettings' | 'admin', data: IUserData) => {
            console.log(route);
            if (route == 'admin' && !data.isAdmin) return false
            else if (route == 'koRequests' && !('requestsData' in data)) return false
            // else if (route == 'koRequests' && data.requestsData.ko.length == 1) return false
            return true
        }

        return {
            userData,
            sidebarLinks,
            activeTab,
            mouseTab,
            tabsCheck: (link: { name: string }) => link.name == 'myRequests' ? ['Статус'] : ['КО', 'Пользователь', 'Статус'],
            checkRights,
        }
    }
});
</script>