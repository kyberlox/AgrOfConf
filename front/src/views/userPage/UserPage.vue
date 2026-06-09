<template>
<div class="p-[80px] bg-white w-full h-full rounded-[16px] border border-(--color-information-gray-100)">
    <div class="text-[20px] font-semibold">
        Персональная информация
    </div>
    <section v-if="userFields[1]?.value">
        <div class="mt-[40px]">
            <div class="w-[80px] h-[80px] rounded-[40px] bg-cover bg-top"
                 :style="{
                    'background-image': `url('${user}')`
                }"></div>
        </div>
        <div class="mt-[48px] grid grid-cols-1 md:grid-cols-1  xl:grid-cols-3 item-center gap-[40px]">
            <div class="flex flex-col gap-[2px]"
                 v-for="(field, index) in userFields"
                 :key="index + 'userField'">
                <div class="text-[13px]">{{ field.label }}</div>
                <div class="text-[16px] p-[16px] bg-[#F6F7F9] rounded-[8px] text-(--text-primary) grow">
                    {{ field.value }}
                </div>
            </div>
        </div>
    </section>
</div>
</template>

<script lang='ts'>
import Api from '@/utils/Api';
import { defineComponent, onMounted, computed } from 'vue';
import { useUserStore } from '@/stores/user';
import { BaseButton } from 'beans-ui-kit';
import DownloadIcon from '@/assets/icons/DownloadIcon.svg?component';
import { type IUser } from '@/assets/interfaces/IUser';

export default defineComponent({
    components: { BaseButton, DownloadIcon },
    props: {},
    setup() {
        const userStore = useUserStore();
        const user = computed(() => userStore.getUser);

        const userFields = computed(() => [
            {
                label: 'ФИО',
                value: userStore.getFio
            },
            {
                label: 'День рождения',
                value: 'dr'
            },
            {
                label: 'Местоположение',
                value: userStore.getUser.work_city
            },
            {
                label: 'Должность',
                value: userStore.getUser.work_position
            },
            {
                label: 'Отдел',
                value: userStore.getUser.department
            },
            {
                label: 'Дирекция',
                value: userStore.getUser.directorate
            },
            {
                label: 'Телефон',
                value: userStore.getUser.work_phone
            },
            {
                label: 'E-mail',
                value: userStore.getUser.email
            },
            {
                label: 'Кабинет',
                value: userStore.getUser.office
            },
        ])

        onMounted(async () => {
            try {
                const user: IUser = await Api.get('users/find_by/4133')
                userStore.setUser(user)
            } catch (error) {
                console.error(error)
            }
        })

        return {
            user,
            userFields
        }
    }
});
</script>