<template>
<div>
    <div class="flex flex-row justify-between items-center mb-[12px]">
        <div class="text-[14px] font-[600] text-[#343B4C]">
            Выберите параметры
        </div>
        <div class="flex flex-row gap-[4px] items-center text-[12px] text-[#8E99A8]">
            <RequiredIcon />
            <div>— обязательные поля</div>
        </div>
    </div>
    <div class="border-t border-[#EAECEF] w-full max-w-full mb-[20px]"></div>
    <!-- Группы параметров  -->
    <MasonryWall v-if="Object.keys(testParamsWithGroups).length"
                 :items="Object.keys(testParamsWithGroups)"
                 :columnWidth="320"
                 :gap="12">
        <template #default="{ item }">
            <div class="masonry-item rounded-[10px] p-[12px] border border-[#EAECEF] transition-all duration-200">
                <!-- Заголовок группы -->
                <div
                     class="text-[13px] font-[600] text-[#5E697D] uppercase tracking-[0.03em] mb-[10px] pb-[8px] border-b border-[#EAECEF]">
                    {{ item }}
                </div>
                <!-- Параметры группы -->
                <EngineParamsGroup :items="getParamsGroup(testParamsWithGroups[item as keyof typeof testParamsWithGroups])
                    .filter(paramsFilter)"
                                   :gridCols="gridCols"
                                   :paramsLoading="paramsLoading"
                                   @valueChanged="(value, param) => $emit('valueChanged', value, param)" />
            </div>
        </template>
    </MasonryWall>
    <!-- Параметры скопом -->
    <EngineParamsNoGroup v-else
                         :form="form"
                         :type="type"
                         :paramsLoading="paramsLoading"
                         @valueChanged="(value, param) => $emit('valueChanged', value, param)" />
</div>
</template>
<script lang='ts'>
import { defineComponent, computed } from 'vue';
import ParamsHeaderIcons from './ParamsHeaderIcons.vue';
import type { IFormattedData } from '@/assets/interfaces/IForm';
import { createLabelIconsComponent } from '@/composables/createComponent';
import { useWindowSize } from '@vueuse/core'
import RequiredIcon from '@/assets/icons/RequiredIcon.svg?component';
import SelectInput from '@/components/SelectInput.vue';
import { BaseInput, BaseSelect } from 'beans-ui-kit';
import { screenMixins } from '@/assets/static/screenMixins';
import EngineParamsGroup from './EngineParamsGroup.vue';
import EngineParamsNoGroup from './EngineParamsNoGroup.vue';
import { MasonryWall } from '@yeger/vue-masonry-wall'

export default defineComponent({
    components: {
        BaseSelect,
        ParamsHeaderIcons,
        RequiredIcon,
        EngineParamsGroup,
        EngineParamsNoGroup,
        SelectInput,
        BaseInput,
        MasonryWall
    },
    props: {
        form: {
            type: Array<IFormattedData>,
            requied: true
        },
        type: {
            type: String,
            default: 'auto'
        },
        paramsLoading: {
            type: Boolean,
            defaul: false
        }
    },
    emits: ['valueChanged'],
    setup(props) {
        const { width } = useWindowSize();
        const gridCols = computed(() => width.value < screenMixins.xxl ? 1 : 2);

        const testParamsWithGroups = {
            // 'Паспортичка': ['ФИО Заказчика', 'Email Заказчика', 'Организация Заказчика', 'Проектная организация', 'Комментарий', 'Должность Заказчика', 'Адрес Заказчика'],
            // 'Паспортичка2': ['ФИО Заказчика', 'Email Заказчика', 'Организация Заказчика', 'Проектная организация', 'Комментарий', 'Должность Заказчика', 'Адрес Заказчика'],
            // 'Группа 2': ['ФИО Заказчика', 'Email Заказчика', 'Организация Заказчика', 'Проектная организация', 'Комментарий',],
            // 'Группа 3': ['Температура рабочей среды максимальная, °C'],
            // 'Группа 4': ['Температура рабочей среды максимальная, °C'],
        }

        const getParamsGroup = (paramGroup: Array<string>) => {
            const newGroup: IFormattedData[] = [];
            paramGroup.forEach(nameInGroup => {
                const target = props?.form?.find(e => e.name == nameInGroup);
                if (target)
                    newGroup.push(target)
            })
            return newGroup;
        }

        return {
            gridCols,
            screenMixins,
            testParamsWithGroups,
            getParamsGroup,
            createLabelIconsComponent,
            paramsFilter: (e: IFormattedData) => e.visibility && e.required_type !== 'raschet' && (e.required_type == 'select-input' ? e.all_values : true)
        }
    }
});
</script>

<style scoped>
.masonry-item {
    width: 100%;
}
</style>
