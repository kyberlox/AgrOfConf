<template>
<div class="w-full grow">
    <div class="text-(--orange) text-[16px] font-semibold"
         v-if="section">
        {{ section }}
    </div>
    <!-- Кнопки навигации и поиск-->
    <div class="min-h-screen mt-[32px] flex flex-col gap-[24px] bg-[#FDFDFD] border  border-[#EAECEF] rounded-[16px]">
        <div class="flex flex-row mt-[32px] gap-[24px] justify-between px-[24px] flex-wrap">
            <div class="flex flex-row gap-[24px] border-b-[1px] border-b-[#EAECEF] flex-grow flex-wrap">
                <RouterLink v-for="item in tableNav"
                            :to="{ name: item.routeName }"
                            class="flex flex-row  items-center relative cursor-pointer px-[24px] hover:text-(--text-primary) duration-300"
                            :class="type == item.name ? 'text-(--text-primary)' : 'text-(--text-secondary)'"
                            :key="item.id + 'tableNav'">
                    <!-- Иконка -->
                    <Component :is="item.icon"
                               class="w-[24px] h-[24px] mr-[8px]">
                    </Component>
                    <!-- Название -->
                    <div>
                        {{ item.title }}
                    </div>
                    <span v-if="type == item.name"
                          class="tableNav"></span>
                </RouterLink>
            </div>
            <!-- Поиск -->
            <BaseInput :propsClass="'searchInput'"
                       :propsPlaceholder="'Поиск'"
                       :type="'search'">
                <template #input-icon>
                    <SearchIcon />
                </template>
            </BaseInput>
        </div>
        <!-- Создать запрос -->
        <div class="flex items-center justify-end w-full px-[24px]"
             v-if="!blankHistory">
            <BaseButton :props-class="'button-primary'"
                        @clicked="showEngineModal = true">
                <Blank class="w-[24px] h-[24px]" />
                <span> Создать ОЛ</span>
            </BaseButton>
        </div>
        <!--  Таблица запросов-->
        <div class=" overflow-x-auto">
            <table class="w-full table-auto">
                <thead>
                    <tr class="bg-[#F6F7F9] h-[56px]">
                        <th class="text-left text-sm font-medium first:pl-[48px] last:pr-[24px] not-first:not-last:p-[5px]"
                            v-for="item in tableHead"
                            :key="item">
                            <div class="flex items-center">
                                <span class="truncate">{{ item }}</span>
                                <ArrowDown class="flex-shrink-0 ml-[9px]" />
                            </div>
                        </th>
                    </tr>
                </thead>
                <tbody v-if="numericPlugs">
                    <tr class="bg-white  overflow-x-auto max-w-screen h-[56px]">
                        <th class="px-[48px] text-left text-sm font-medium mr-[15px]"
                            v-for="(item, index) in numericPlugs"
                            :key="item">
                            <div class="flex items-center">
                                <span class="truncate"
                                      :class="index == 0 ? 'underline cursor-pointer hover:text-[var(--orange)] duration-300 transition' : ''">{{
                                        item
                                    }}
                                </span>
                            </div>
                        </th>
                    </tr>
                </tbody>
            </table>
        </div>
        <!-- Заглушка если нет истории -->
        <div v-if="blankHistory && currentTableNav == 'requests'"
             class="2xl:mt-[40px] xl:mt-[20px] ">
            <EmptyHistoryPlug @createOl="showEngineModal = true" />
        </div>
        <!-- Модалка для выбора изделия -->
        <SlotModal v-if="showEngineModal"
                   @closeModal="showEngineModal = false">
            <EnginePick :items="engines" />
        </SlotModal>

    </div>
</div>
</template>
<script lang='ts'>
import { defineComponent, onMounted, ref, computed, type Ref, type PropType, watch } from 'vue';
import { tableNav } from '@/assets/static/tableNav';
import { BaseButton, BaseInput } from 'beans-ui-kit';
import SearchIcon from '@/assets/icons/SearchIcon.svg?component';
import Blank from '@/assets/icons/Blank.svg?component';
import ArrowDown from '@/assets/icons/ArrowDown.svg?component';
import EmptyHistoryPlug from '@/components/EmptyHistoryPlug.vue';
import SlotModal from '@/components/layout/SlotModal.vue';
import Api from '@/utils/Api';
import EnginePick from '@/views/homeView/components/EnginePick.vue'
import Configurator from '../configurator/Configurator.vue';
import { RouterLink } from 'vue-router';
import { useProductsData } from '@/stores/products';

export default defineComponent({
    components: {
        BaseInput,
        BaseButton,
        Blank,
        ArrowDown,
        SearchIcon,
        EmptyHistoryPlug,
        SlotModal,
        EnginePick,
        Configurator,
        RouterLink
    },
    props: {
        type: {
            type: String as PropType<'requests' | 'statistics'>,
            default: 'requests'
        }
    },
    setup(props) {
        const blankHistory = ref(true);
        const showEngineModal = ref(false);
        const tableHeadRequests = ['Шифр ОЛ', 'ОЛ №', 'Статус', 'Документ №', 'Готовность', 'Наименование', 'Шт.', 'Комментарий', 'Созд.', 'Готов'];
        const tableHeadStatistics = ['КО', 'ОЛ за мес.', 'ОЛ за год', 'ОЛ за все время', 'Запросов за мес.', 'Запросов за тек. мес.', 'Запросов за год', 'Запросов за все время']
        const engines = ref([]);
        const engineId = ref();
        const section = ref('Тест');
        const currentTableNav: Ref<'requests' | 'statistics'> = ref(props.type);

        watch(props, () => {
            if (props.type) currentTableNav.value = props.type;
        })

        onMounted(() => {
            Api.get('products/?skip=0&limit=100')
                .then((data) => {
                    useProductsData().setProducts(data);
                    engines.value = data;
                })
        })

        return {
            engineId,
            tableNav,
            blankHistory,
            showEngineModal,
            engines,
            section,
            currentTableNav,
            tableHead: computed(() => props.type == 'requests' ? tableHeadRequests : tableHeadStatistics),
            numericPlugs: computed(() => props.type == 'statistics' ? ['Старый оскол', 60, 21, 450, 50, 5650, 5643150, 564314150] : [])
        }
    }
});
</script>