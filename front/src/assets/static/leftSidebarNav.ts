import UserIcon from '@/assets/icons/UserIcon.svg?component';
import TeamIcon from '@/assets/icons/TeamIcon.svg?component';
import SettingsIcon from '@/assets/icons/Settings.svg?component';
import AdminIcon from '@/assets/icons/UserAdmin.svg?component';

export const sidebarLinks = [
    {
        name: 'myRequests',
        title: 'Мои запросы',
        icon: UserIcon,
        route: 'myRequests'
    },
    {
        name: 'koRequests',
        title: 'Запросы КО',
        icon: TeamIcon,
        route: 'koRequests'
    },
    {
        name: 'profileSettings',
        title: 'Мой профиль',
        icon: SettingsIcon,
        route: 'user'
    },
    {
        name: 'admin',
        title: 'Администрирование',
        icon: AdminIcon,
        route: 'admin'
    },
]