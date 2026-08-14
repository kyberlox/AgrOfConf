<template>
<SlotModal v-if="showModal">
    <div class="flex flex-col gap-2 p-4 min-w-full cursor-default">
        <div class="flex flex-col"
             v-for="(param, index) in params.filter(e => e !== 'id')"
             :key="index + 'input'">
            <VInputFile v-if="param == 'image'"
                        :button-class="'button-primary'"
                        @fileUpload="(image: string) => updateUserInputs('image', image)" />

            <BaseInput v-else
                       :inputSettings="initInputProps(param as keyof IProduct)"
                       @valueChanged="(val: string) => updateUserInputs(param as keyof IProduct, val)" />
        </div>
        <div class="flex justify-start">
            <BaseButton :button-settings="{ class: 'button-primary' }"
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
        showModal: {
            type: Boolean,
            default: false
        }
    },
    emits: ['closeAllModals', 'deleteProduct', 'changeProduct'],
    setup(props) {
        const userInputs = ref<IProduct>({} as IProduct);

        watch(() => props.product, () => {
            if (props.type == 'add') return
            userInputs.value = { ...props.product };
        }, { immediate: true })

        type ProductKey = keyof IProduct;
        const updateUserInputs = <K extends ProductKey>(key: K, value: IProduct[K]) => {
            if ((typeof value == 'string' && value && value !== 'null') || value === '') {
                userInputs.value[key] = value;
            }
        }
        const params = ref(Object.keys(userInputs.value));

        const initInputProps = (param: keyof IProduct) => {
            return {
                class: 'input-product-edit',
                placeholder: param,
                label: param,
                value: userInputs.value[param]
            }
        }

        return {
            params,
            userInputs,
            updateUserInputs,
            initInputProps
        }
    }
});
</script>