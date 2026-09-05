<template>
<div class="h-[88vh] bg-white p-[32px] rounded-lg w-full">
    <div class="flex justify-end">
        <BaseButton :buttonSettings="{ class: 'button-primary' }"
                    @click="showAddModal = true">
            Добавить
        </BaseButton>
    </div>

    <div class="flex flex-row gap-[16px] mt-[10px]">
        <div class="cursor-pointer bg-white relative "
             v-for="product in products"
             :key="product.id">
            <RouterLink class="w-[200px] h-[274] p-[17px] cursor-pointer flex flex-col gap-[10px] border border-[#EAECEF] rounded-[8px] h-full hover:border-orange-500 duration-300 transition-all"
                        :to="{ name: 'productEdit', params: { id: product.id } }">
                <div class="bg-contain bg-no-repeat bg-center w-full h-[170px]"
                     :style="{ 'background-image': `url(${product.image_url})` }">
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
                <div class="mt-auto p-4">
                    <div class="flex flex-row gap-2 items-center justify-end mt-auto h-full group">
                        <MoreIcon />
                        <MoreOptions class="hidden group-hover:block!"
                                     :list="['Изменить', 'Удалить']"
                                     @valueClicked="(value: string) => handleValueClick(value, product)" />
                    </div>
                </div>
            </RouterLink>
        </div>
    </div>

    <!-- Модалка удаления -->
    <ProductDeleteModal v-if="selectedProduct"
                        :showDeleteModal="showDeleteModal"
                        :product="selectedProduct"
                        :isLoading="isLoading"
                        @closeAllModals="closeAllModals"
                        @deleteProduct="deleteProduct" />

    <!-- Модалка редактирования -->
    <ProductParamsModal v-if="selectedProduct"
                        :showModal="showEditModal"
                        :product="selectedProduct"
                        :type="'edit'"
                        :isLoading="isLoading"
                        @closeModal="closeAllModals"
                        @changeProduct="changeProduct" />

    <!-- Модалка добавления -->
    <ProductParamsModal :showModal="showAddModal"
                        :type="'add'"
                        :isLoading="isLoading"
                        @closeModal="closeAllModals"
                        @changeProduct="changeProduct" />
</div>
</template>
<script lang='ts'>
import Api from '@/utils/Api';
import { defineComponent, onMounted, ref } from 'vue';
import MoreIcon from '@/assets/icons/MoreIcon.svg?component';
import MoreOptions from '@/components/layout/MoreOptions.vue';
import SlotModal from '@/components/layout/SlotModal.vue';
import { type IProduct } from '@/assets/interfaces/IProduct';
import ProductDeleteModal from './ProductDeleteModal.vue';
import ProductParamsModal from './ProductParamsModal.vue';
import { BaseButton } from 'beans-ui-kit';

interface IProductForm {
    name: string,
    manufacturer: string,
    description: string,
    image?: string
}

export default defineComponent({
    components: {
        MoreIcon,
        MoreOptions,
        SlotModal,
        ProductDeleteModal,
        ProductParamsModal,
        BaseButton
    },
    props: {},
    setup() {
        const products = ref<IProduct[]>([]);
        const selectedProduct = ref<IProduct | null>(null);
        const showEditModal = ref(false);
        const showDeleteModal = ref(false);
        const showAddModal = ref(false);
        const isLoading = ref(false);

        onMounted(() => {
            initProducts();
        })

        const initProducts = async () => {
            try {
                const data = await Api.get('products/?skip=0&limit=1000')
                products.value.length = 0;
                products.value = data
            }
            catch (error) { console.error(error) }
        }

        const handleValueClick = (value: string, product: IProduct) => {
            selectedProduct.value = product;
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

        const changeProduct = (type: string, id: number | null, userInputs: IProductForm) => {
            switch (type) {
                case 'add':
                    addProduct(userInputs);
                    break;
                case 'edit':
                    if (!id) return
                    editProduct(id, userInputs)
                    break
                default:
                    break;
            }
        }

        const addProduct = async (userInputs: IProductForm) => {
            isLoading.value = true;
            const formInput = new FormData();
            formInput.append('name', userInputs.name);
            formInput.append('description', userInputs.description || '');
            formInput.append('manufacturer', userInputs.manufacturer || '');
            if (userInputs.image) {
                formInput.append('image', userInputs.image);
            }
            try {
                await Api.post('products/', formInput)
            } catch (error) {
                console.error(error)
            } finally {
                closeAllModals()
                initProducts();
                isLoading.value = false
            }
        }

        const editProduct = async (id: number, userInputs: IProductForm) => {
            isLoading.value = true;
            const formInput = new FormData();
            formInput.append('name', userInputs.name);
            formInput.append('description', userInputs.description || '');
            formInput.append('manufacturer', userInputs.manufacturer || '');
            try {
                await Api.put(`products/${id}`, formInput)
            } catch (error) {
                console.error(error)
            } finally {
                closeAllModals();
                initProducts();
                isLoading.value = false;
            }
        }

        const deleteProduct = async (id: number) => {
            isLoading.value = true;
            try {
                await Api.delete(`products/${id}`)
            }
            catch (error) {
                console.error(error)
            }
            finally {
                closeAllModals();
                initProducts();
                isLoading.value = false;
            }
        }

        return {
            products,
            selectedProduct,
            showEditModal,
            showDeleteModal,
            showAddModal,
            isLoading,
            handleValueClick,
            closeAllModals,
            deleteProduct,
            addProduct,
            editProduct,
            changeProduct
        }
    }
});
</script>