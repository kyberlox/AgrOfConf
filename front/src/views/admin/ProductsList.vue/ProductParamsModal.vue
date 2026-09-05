<template>
<div v-if="showModal"
     class="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
    <div class="bg-white rounded-lg p-6 w-full max-w-md shadow-xl">
        <h1 class="text-lg font-medium mb-4">
            {{ type == 'edit' ? 'Редактирование продукта' : 'Добавление продукта' }}
        </h1>

        <div class="flex flex-col gap-3">
            <label class="flex flex-col gap-1 text-sm">
                <span class="text-gray-700">Название</span>
                <input class="input-product-edit w-full"
                       v-model="userInputs.name"
                       placeholder="Название" />
            </label>

            <label class="flex flex-col gap-1 text-sm">
                <span class="text-gray-700">Производитель</span>
                <input class="input-product-edit w-full"
                       v-model="userInputs.manufacturer"
                       placeholder="Производитель" />
            </label>

            <label class="flex flex-col gap-1 text-sm">
                <span class="text-gray-700">Описание</span>
                <input class="input-product-edit w-full"
                       v-model="userInputs.description"
                       placeholder="Описание" />
            </label>

            <label class="flex flex-col gap-1 text-sm">
                <span class="text-gray-700">Изображение</span>
                <input type="file"
                       accept="image/*"
                       @change="onFileChange" />
            </label>
        </div>

        <div class="flex justify-end gap-3 mt-5">
            <button class="px-4 py-2 rounded bg-gray-200 hover:bg-gray-300"
                    @click="$emit('closeModal')">
                Назад
            </button>
            <button class="px-4 py-2 rounded text-white bg-orange-500 hover:bg-orange-600 disabled:opacity-50"
                    :disabled="!userInputs.name || isLoading"
                    @click="$emit('changeProduct', type, product?.id ?? null, userInputs)">
                {{ type == 'edit' ? 'Изменить' : 'Добавить' }}
            </button>
        </div>
    </div>
</div>
</template>
<script lang='ts'>
import { defineComponent, reactive, watch, type PropType } from 'vue';
import { type IProduct } from '@/assets/interfaces/IProduct';

interface IProductForm {
    name: string,
    manufacturer: string,
    description: string,
    image?: string
}

const emptyForm = (): IProductForm => ({ name: '', manufacturer: '', description: '' });

export default defineComponent({
    props: {
        type: {
            type: String as PropType<'add' | 'edit'>
        },
        product: {
            type: Object as PropType<IProduct>,
            default: null
        },
        isLoading: {
            type: Boolean
        },
        showModal: {
            type: Boolean,
            default: false
        }
    },
    emits: ['closeModal', 'changeProduct'],
    setup(props) {
        const userInputs = reactive<IProductForm>(emptyForm());

        watch(() => props.showModal, () => {
            if (!props.showModal) return
            if (props.type == 'edit' && props.product) {
                userInputs.name = props.product.name ?? ''
                userInputs.manufacturer = props.product.manufacturer ?? ''
                userInputs.description = props.product.description ?? ''
                userInputs.image = undefined
            } else {
                Object.assign(userInputs, emptyForm())
            }
        }, { immediate: true })

        const onFileChange = (event: Event) => {
            const input = event.target as HTMLInputElement
            const file = input.files?.[0]
            if (!file) return
            const reader = new FileReader()
            reader.onload = () => {
                userInputs.image = String(reader.result ?? '')
            }
            reader.readAsDataURL(file)
        }

        return {
            userInputs,
            onFileChange
        }
    }
});
</script>