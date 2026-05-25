<template>
<div class="min-h-screen bg-white p-2 rounded-lg w-full p-[16px]">
    <div class="flex flex-row justify-start gap-[25px]  flex-wrap ">
        <div class="max-w-full lg:max-w-[40%] p-4 bg-blue-50 border border-blue-200 rounded-lg shadow-sm">
            <div class="text-lg text-blue-800 font-medium mb-2 grow">
                Информация о редактировании
            </div>
            <div class="text-md text-gray-700">
                Для изменения логики подбора по табличным параметрам необходимо
                отредактировать исходный
                excell
                файл, сперва скачав его, отредактировав и затем загрузив по кнопкам в блоке Excell, добавить или
                отредактировать формульные параметры можно по нажатию на блок или кнопку "+"
            </div>
        </div>
        <div class="flex justify-start gap-2">
            <div
                 class="flex flex-row flex-wrap md:flex-nowrap  gap-2 items-center border border-green-300 bg-green-100 rounded-md p-4">
                <div class="text-lg w-full">
                    Excell
                </div>
                <BaseButton @click="downloadExcell"
                            :propsClass="'button-primary'">
                    Скачать
                </BaseButton>
                <BaseButton @click="excellFileNode.click()"
                            :propsClass="'button-primary'">
                    {{ excellFileNode?.files[0]?.name ?? 'Загрузить' }}
                </BaseButton>
                <input class="hidden"
                       @change="handleExcellUpload"
                       ref="excellFileNode"
                       type="file" />
            </div>
        </div>
        <div class="w-fit m-auto">
            <Transition name="fade-btn">
                <BaseButton v-if="sortChanged"
                            :propsClass="'button-primary'"
                            @clicked="sendNewSort">
                    Принять сортировку
                </BaseButton>
            </Transition>
        </div>
    </div>
    <div class="flex flex-col gap-[20px]">
        <div class="flex flex-col gap-2 mt-4 border border-gray-200 p-[20px] rounded-xl"
             v-if="productTableType.length">
            <div class="flex flex-row justify-left gap-[40px] flex-wrap">
                <div v-for="item in ['Табличные параметры - ', 'Формульные параметры - ']"
                     class="flex flex-row gap-[15px]">
                    <h3 class="block">{{ item }}</h3>
                    <div class="w-[20px] h-[20px] rounded-md"
                         :class="item.includes('Табл') ? 'bg-green-200' : 'bg-blue-200'"></div>
                </div>
            </div>
            <div class="">
                <VueDraggable v-model="productTableType"
                              :animation="150"
                              target=".sort-target"
                              @start="onStart"
                              @end="onEnd">
                    <TransitionGroup type="transition"
                                     tag="ul"
                                     :name="!drag ? 'fade' : undefined"
                                     class="sort-target grid grid-cols-1 sm:grid-cols-1 md:grid-cols-1 lg:grid-cols-4 gap-4 max-w-full mt-4">
                        <li v-for="(parameter, index) in productTableType"
                            :key="parameter.id"
                            class="flex flex-col py-[20px] px-[15px]  border border-green-200 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 bg-green-50 relative cursor-move"
                            :class="{ 'bg-blue-50! border-blue-200!': parameter.type == 'Formula' }">
                            <div class="text-lg pr-[25px] font-medium  text-gray-800 mb-2 wrap-break-word">
                                {{ parameter.name }}
                            </div>
                            <div class="text-sm text-gray-600 mb-3 wrap-break-word">
                                {{ parameter.description }}
                            </div>
                            <!-- <div class="text-xs text-gray-500 text-right mb-1">Тип: {{ parameter.type }}</div> -->
                            <div class="text-xs text-gray-500  wrap-break-word">
                                Из таблицы: {{ parameter.table_name }}
                            </div>
                            <div class="w-[24px] h-[24px] p-[5px] rounded-lg bg-mist-100 absolute top-[15px] right-[15px] cursor-pointer hover:bg-mist-300 text-[var(--icon-color-secondary)] hover:text-[var(--icon-color-primary)]"
                                 @click.stop.prevent="changeSettings(parameter.id)">
                                <SettingsIcon />
                            </div>
                        </li>
                    </TransitionGroup>
                </VueDraggable>
            </div>
        </div>
    </div>
    <ParameterSettings v-if="productSettingsVisible"
                       :parameter="productTableType.find(e => e.id == idInSettings)"
                       :disabled="parameterUpdating"
                       @updateParameter="(id, parameter) => updateParameter(id, parameter)"
                       @closeModal="{ productSettingsVisible = false; idInSettings = false }" />
</div>
</template>
<script lang='ts'>
import Api from '@/utils/Api';
import { defineComponent, onMounted, ref, computed, TransitionGroup, nextTick } from 'vue';
import SlotModal from '@/components/layout/SlotModal.vue';
import download from 'downloadjs';
import { BaseButton } from 'beans-ui-kit';
import CloseIcon from '@/assets/icons/Cross.svg?component';
import Plus from '@/assets/icons/Plus.svg?component';
import { useProductsData } from '@/stores/products';
import { startDrag, onOver, onLeave, onDrop } from '@/utils/DragEvents';
import SettingsIcon from '@/assets/icons/Settings.svg?component';
import ParameterSettings from './ParameterSettings.vue';
import type { IParameter } from '@/assets/interfaces/IParameter';
import type { IProduct } from '@/assets/interfaces/IProduct';

export default defineComponent({
    components: {
        SlotModal,
        BaseButton,
        CloseIcon,
        Plus,
        TransitionGroup,
        SettingsIcon,
        ParameterSettings
    },
    props: {
        id: {
            type: String,
            requied: true
        }
    },
    setup(props) {
        const productTableType = ref<IParameter[]>([]);
        const product = computed(() => useProductsData().getProducts.find(e => e.id == Number(props.id)))
        const list = ref();
        const url = import.meta.env.VITE_API_URL;
        const excellFileNode = ref();
        const drag = ref(false);
        const sortChanged = ref(false);
        const productSettingsVisible = ref(false);
        const idInSettings = ref();
        const parameterUpdating = ref(false);

        const downloadExcell = () => {
            Api.post(`tables/download_xlsx?product_id=${props.id}`, undefined, { responseType: 'blob' })
                .then((data) => download(data.data, String(data.headers['content-disposition'].split('=')[1]).replaceAll('"', ''), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
        }

        const handleExcellUpload = () => {
            const excell = excellFileNode.value.files[0];
            const body = new FormData();
            body.append('file', excell);
            Api.post(`tables/upload_xlsx?product_id=${props.id}`, body)
                .then(() => getParams())
        }

        const getParams = () => {
            Api.get(`parameters/by_product/${props.id}`)
                .then((data: IParameter[] | { detail: string }) => {
                    if (!data || 'detail' in data) productTableType.value = []
                    productTableType.value = (data as IParameter[]).sort((a, b) => Number(a['sort']) - Number(b['sort']));
                })
                .catch(() => productTableType.value = [])
        }

        const getUserInputType = () => {
            Api.get('http://agrofconf.emk.org.ru/api/user_input/get_user_inputs')
        }

        // const addParam = () => {
        //     const newBody = {};
        //     Api.post('api/parameters/', newBody)
        //         .then(() => getParams())
        // }

        onMounted(() => {
            getParams();
        })

        const deleteParam = () => {
            console.log('del')
        }

        const onStart = () => {
            sortChanged.value = true;
            drag.value = true;
        }

        const onEnd = () => {
            nextTick(() => {
                drag.value = false
            })
        }

        const sendNewSort = () => {
            sortChanged.value = false;
            const newBody: IParameter[] = productTableType.value.map((e, index) => {
                e.sort = index + 1;
                return e
            })
            Api.put(`/parameters/sort/${props.id}`, newBody)
                .catch((err) => console.log(err))
        }

        const changeSettings = (id: number) => {
            productSettingsVisible.value = true;
            idInSettings.value = id;
        }

        const updateParameter = (id: number, parameter: { name: string, description: string }) => {
            parameterUpdating.value = true;
            Api.put(`parameters/${id}`, parameter)
                .then(() => parameterUpdating.value = false)
                .finally(() => {
                    getParams();
                    productSettingsVisible.value = false
                })
        }

        return {
            url,
            productTableType,
            excellFileNode,
            product,
            list,
            sortChanged,
            drag,
            productSettingsVisible,
            idInSettings,
            parameterUpdating,
            // addParam,
            downloadExcell,
            sendNewSort,
            handleExcellUpload,
            deleteParam,
            startDrag,
            onOver,
            onLeave,
            onDrop,
            onStart,
            onEnd,
            changeSettings,
            updateParameter,
        }
    }
});
</script>

<style>
.fade-move,
.fade-enter-active,
.fade-leave-active {
  transition: all 0.5s cubic-bezier(0.55, 0, 0.1, 1);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: scaleY(0.01) translate(30px, 0);
}

.fade-leave-active {
  position: absolute;
}

.fade-btn-enter-active,
.fade-btn-leave-active {
  transition: opacity 0.3s ease;
}

.fade-btn-enter-from,
.fade-btn-leave-to {
  opacity: 0;
}
</style>
