<template>
<SlotModal v-if="showAddModal">
    <div class="flex flex-col gap-2 p-4 min-w-full cursor-default">
        <div class="flex flex-col"
             v-for="(param, index) in params.filter(e => e !== 'id')"
             :key="index + 'input'">
            <VInputFile v-if="param == 'image'"
                        @fileUpload="(image: string) => updateUserInputs('image', image)" />

            <BaseInput v-else
                       :propsClass="'input-product-edit'"
                       :propsPlaceholder="param"
                       :propsLabel="param"
                       :propsValue="userInputs[param as keyof IProduct]"
                       @valueChanged="(x) => updateUserInputs(param as keyof IProduct, x)" />
        </div>
        <div class="flex justify-start">
            <BaseButton :props-class="'button-primary'"
                        @click="$emit('changeProduct', type, product.id ?? null, userInputs)">
                <div class="w-[20px] h-[20px]"
                     v-if="isLoading">
                    <Loader />
                </div>
                <span v-else>{{ type == 'edit' ? 'Изменить' : 'Добавить' }}</span>
            </BaseButton>
        </div>
    </div>
</SlotModal>
</template>
<script lang='ts'>
import { defineComponent, watch, type PropType } from 'vue';
import { type IProduct } from '@/assets/interfaces/IProduct';
import { ref } from 'vue';
import VInputFile from '@/components/layout/VInputFile.vue';
import Loader from '@/components/layout/Loader.vue';
import { BaseButton, BaseInput } from 'beans-ui-kit';
import SlotModal from '@/components/layout/SlotModal.vue';

export default defineComponent({
    components: {
        BaseButton,
        VInputFile,
        Loader,
        BaseInput,
        SlotModal
    },
    props: {
        type: {
            type: String
        },
        product: {
            type: Object as PropType<IProduct>,
            default: {
                created_at: '',
                description: '',
                image: '',
                manufacturer: '',
                name: ''
            }
        },
        isLoading: {
            type: Boolean
        },
        showAddModal: {
            type: Boolean,
            default: false
        }
    },
    emits: ['closeAllModals', 'deleteProduct', 'changeProduct'],
    setup(props) {
        const userInputs = ref<IProduct>({} as IProduct);

        watch(() => props.product, () => {
            userInputs.value = { ...props.product };
        }, { immediate: true })

        type ProductKey = keyof IProduct;
        const updateUserInputs = <K extends ProductKey>(key: K, value: IProduct[K]) => {
            if ((typeof value == 'string' && value && value !== 'null') || value === '') {
                userInputs.value[key] = value;
            }
        }
        const params = ref(Object.keys(userInputs.value));

        return {
            params,
            userInputs,
            updateUserInputs
        }
    }
});
</script>