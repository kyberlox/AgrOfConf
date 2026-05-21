<template>
<div class="h-screen bg-white p-[32px] rounded-lg w-full">
    <div class="flex justify-end">
        <BaseButton @click="showAddModal = true"
                    :propsClass="'button-primary'"
                    :propsTitle="'Добавить'">
            Добавить
        </BaseButton>
    </div>
    <div class="flex flex-row gap-[16px]">
        <div class="cursor-pointer bg-white relative "
             v-for="product in products"
             :key="product.id">
            <RouterLink class="w-[200px] h-[274] p-[17px] cursor-pointer flex flex-col gap-[10px] border border-[#EAECEF] rounded-[8px] hover:border-orange-500 duration-300 transition-all"
                        :to="{ name: 'productEdit', params: { id: product.id } }">
                <div class="bg-contain bg-no-repeat bg-center w-full h-[170px]"
                     :style="{ 'background-image': `url(http://agrofconf.emk.org.ru${product.image_url})` }">
                </div>
                <div class="text-[14px] text-(--text-primary)">
                    {{ product.name }}
                </div>
                <div class="text-[13px] text-(--text-secondary) text-[600]">
                    {{ product.manufacturer }}
                </div>
                <div class="text-[11px] text-(--text-secondary)">
                    {{ product.description }}
                </div>
                <div class="mt-2 p-4 grow">
                    <div class="flex flex-row gap-2 items-center justify-end group mt-auto h-full">
                        <MoreIcon />
                        <MoreOptions class="hidden group-hover:block"
                                     :list="['Изменить', 'Удалить']"
                                     @valueClicked="handleValueClick" />
                    </div>
                </div>
            </RouterLink>
            <SlotModal v-if="showDeleteModal || showEditModal"
                       @closeModal="closeAllModals">
                <ProductDeleteModal v-if="showDeleteModal"
                                    :product="product"
                                    :isLoading="isLoading"
                                    @closeAllModals="closeAllModals"
                                    @deleteProduct="deleteProduct" />
                <ProductParamsModal v-else-if="showEditModal"
                                    :product="product"
                                    :type="'edit'"
                                    :isLoading="isLoading"
                                    @changeProduct="changeProduct" />
            </SlotModal>
        </div>
    </div>
    <SlotModal v-if="showAddModal"
               @closeModal="closeAllModals">
        <ProductParamsModal :type="'add'"
                            :isLoading="isLoading"
                            @changeProduct="changeProduct" />
    </SlotModal>
</div>
</template>
<script lang='ts'>
import Api from '@/utils/Api';
import { defineComponent, onMounted, ref } from 'vue';
import MoreIcon from '@/assets/icons/MoreIcon.svg?component';
import SettingIcon from '@/assets/icons/Settings.svg?component';
import MoreOptions from '@/components/layout/MoreOptions.vue';
import SlotModal from '@/components/layout/SlotModal.vue';
import { type IProduct } from '@/assets/interfaces/IProduct';
import ProductDeleteModal from './ProductDeleteModal.vue';
import ProductParamsModal from './ProductParamsModal.vue';
import { BaseButton } from 'beans-ui-kit';

export default defineComponent({
    components: {
        MoreIcon,
        SettingIcon,
        MoreOptions,
        SlotModal,
        ProductDeleteModal,
        ProductParamsModal,
        BaseButton
    },
    props: {},
    setup() {
        const products = ref<IProduct[]>([]);
        const url = import.meta.env.VITE_API_URL;
        const showOptions = ref(false);
        const showEditModal = ref(false);
        const showDeleteModal = ref(false);
        const showAddModal = ref(false);
        const isLoading = ref(false);

        onMounted(() => {
            initProducts();
        })

        const initProducts = () => {
            Api.get('products/?skip=0&limit=1000')
                .then((data) => { products.value.length = 0; products.value = data })
        }

        const handleValueClick = (value: string) => {
            switch (value) {
                case 'Изменить':
                    showEditModal.value = true;
                    break;

                case 'Удалить':
                    showDeleteModal.value = true;
                    break;

                default:
                    break;
            }
        }

        const closeAllModals = () => {
            showDeleteModal.value = false;
            showEditModal.value = false;
            showAddModal.value = false;
        }

        const changeProduct = (type: string, id: number, userInputs: IProduct) => {
            switch (type) {
                case 'add':
                    addProduct(userInputs);
                    break;
                case 'edit':
                    if (!id) return
                    editProduct(id, userInputs)
                    break
                case 'delete':
                    if (!id) return
                    deleteProduct(id)
                default:
                    break;
            }
        }

        const addProduct = (userInputs: IProduct) => {
            isLoading.value = true;
            const formInput = new FormData();
            Object.keys(userInputs).forEach(key => formInput.append(key, (userInputs[key as keyof typeof userInputs] as string)))
            Api.post('products/', formInput)
                .then(() => closeAllModals())
                .finally(() => {
                    initProducts();
                    isLoading.value = false
                })
        }

        const editProduct = (id: number, userInputs: IProduct) => {
            isLoading.value = true;
            const formInput = new FormData();
            Object.keys(userInputs).filter(e => e !== 'image' && e !== 'image_url').forEach(key => formInput.append(key, (userInputs[key as keyof typeof userInputs] as string)))
            Api.put(`products/${id}`, formInput)
                .finally(() => {
                    closeAllModals();
                    initProducts();
                    isLoading.value = false;
                })
        }

        const deleteProduct = (id: number) => {
            isLoading.value = true;
            Api.delete(`products/${id}`)
                .then(() => {
                    closeAllModals();
                    initProducts();
                })
                .finally(() => {
                    isLoading.value = false;
                })
        }

        return {
            url,
            products,
            showOptions,
            showEditModal,
            showDeleteModal,
            showAddModal,
            isLoading,
            editProduct,
            handleValueClick,
            closeAllModals,
            deleteProduct,
            addProduct,
            changeProduct
        }
    }
});
</script>