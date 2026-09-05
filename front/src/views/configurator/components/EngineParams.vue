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
    <MasonryWall v-if="paramsGroups && paramsGroups.length"
                 :items="paramsGroups"
                 :columnWidth="400"
                 :gap="12">
        <template #default="{ item, index }">
            <div
                 class="w-full rounded-[10px_10px_0_0] border border-[#EAECEF] transition-all  hover:shadow-lg hover:shadow-gray-200 hover:border-[#d4d4d4]">
                <!-- Заголовок группы -->
                <div class="text-[13px] px-[8px] py-[8px] rounded-[10px_10px_0_0] font-[600] h-full bg-cover bg-blend-multiply bg-right bg-(--color-information-gray-200) text-black uppercase tracking-[0.03em] mb-[2px] border-b border-[#EAECEF] bg-image bg-right"
                     :style="{ backgroundImage: `url(${backImage})`, backgroundPositionY: `${(index + 2) * 25}px` }">
                    {{ item.name }}
                </div>
                <!-- Параметры группы -->
                <EngineParamsGroup :items="getGroupedParams(item)"
                                   :gridCols="gridCols"
                                   :type="type"
                                   :userParams="userParams"
                                   :paramsLoading="paramsLoading"
                                   @resetValue="(param) => $emit('valueChanged', null, param)"
                                   @valueChanged="(value, param) => $emit('valueChanged', value, param)" />
            </div>
        </template>
    </MasonryWall>
    <!-- Параметры скопом -->
    <EngineParamsNoGroup v-else-if="form"
                         :items="form"
                         :gridCols="gridCols"
                         :type="type"
                         :userParams="userParams"
                         :paramsLoading="paramsLoading"
                         @resetValue="(param) => $emit('valueChanged', null, param)"
                         @valueChanged="(value, param) => $emit('valueChanged', value, param)" />
</div>
</template>
<script lang='ts'>
import { defineComponent, computed, type PropType } from 'vue';
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
import { MasonryWall } from '@yeger/vue-masonry-wall';
import backImage from '@/assets/img/test.jpg';

interface IParamBlock {
    name: string;
    display: string;
    params: Array<string>;
}

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
            type: Array as PropType<IFormattedData[]>,
            requied: true
        },
        type: {
            type: String,
            default: 'auto'
        },
        paramsLoading: {
            type: Boolean,
            defaul: false
        },
        paramsGroups: {
            type: Array as PropType<IParamBlock[]>,
            default: () => []
        },
        userParams: {
            type: Object as PropType<Record<string, string>>
        }
    },
    emits: ['valueChanged'],
    setup(props) {
        const { width } = useWindowSize();
        const gridCols = computed(() => width.value < screenMixins.xxl ? 1 : 2);

        const getParamsGroup = (paramGroup?: Array<string>) => {
            if (!paramGroup) {
                return []
            }
            const newGroup: IFormattedData[] = [];
            paramGroup.forEach(nameInGroup => {
                const target = props?.form?.find(e => e.name == nameInGroup);
                if (target)
                    newGroup.push(target)
            })
            return newGroup;
        }

        // Применяем фильтр видимости/доступности и режим отображения блока.
        const paramsFilter = (e: IFormattedData) => e.visibility && e.required_type !== 'raschet' && (e.required_type == 'select-input' ? e.all_values : true)

        // Для режима «sequential» показываем параметры друг за другом:
        // только отвеченные плюс первый неотвеченный. Для «group» — все сразу.
        const getGroupedParams = (block: IParamBlock): IFormattedData[] => {
            const all = getParamsGroup(block.params).filter(paramsFilter);
            if (block.display === 'sequential') {
                const result: IFormattedData[] = [];
                for (const p of all) {
                    result.push(p);
                    const answered = !!(p.response_value || (props.userParams && props.userParams[p.name]));
                    if (!answered) break;
                }
                return result;
            }
            return all;
        }

        return {
            gridCols,
            screenMixins,
            backImage,
            getParamsGroup,
            getGroupedParams,
            createLabelIconsComponent,
            paramsFilter
        }
    }
});
</script>