import UserIcon from '@/assets/icons/UserIcon.svg?component';
import TeamIcon from '@/assets/icons/TeamIcon.svg?component';
import SettingsIcon from '@/assets/icons/Settings.svg?component';
import AdminIcon from '@/assets/icons/UserAdmin.svg?component';

export const sidebarLinks = [
                {
                    name: 'myRequests',
                    title: 'Мои запросы',
                    icon: UserIcon,
                },
                {
                    name: 'koRequests',
                    title: 'Запросы КО',
                    icon: TeamIcon,
                },
                {
                    name: 'profileSettings',
                    title: 'Настройки профиля',
                    icon: SettingsIcon,
                    route: '1'
                },
                {
                    name: 'admin',
                    title: 'Администрирование',
                    icon: AdminIcon,
                    route: 'admin'
                },
            ]