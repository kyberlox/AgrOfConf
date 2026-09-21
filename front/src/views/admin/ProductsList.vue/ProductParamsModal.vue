<template>
    <SlotModal v-if="showModal" @closeModal="$emit('closeModal')">
        <div class="bg-white rounded-lg p-6 w-full max-w-md shadow-xl">
            <h1 class="text-lg font-medium mb-4">
                {{ type == "edit" ? "Редактирование продукта" : "Добавление продукта" }}
            </h1>

            <div class="flex flex-col gap-3">
                <label v-for="field in productFormFields" :key="field.name" class="flex flex-col gap-1 text-sm">
                    <span class="text-gray-700">{{ field.label }}</span>
                    <input
                        class="input-product-edit w-full"
                        v-model="userInputs[field.name]"
                        :placeholder="field.label" />
                </label>

                <label class="flex flex-col gap-1 text-sm">
                    <span class="text-gray-700">Изображение</span>
                    <input type="file" accept="image/*" @change="onFileChange" />
                </label>
            </div>

            <div class="flex justify-end gap-3 mt-5">
                <button class="px-4 py-2 rounded bg-gray-200 hover:bg-gray-300" @click="$emit('closeModal')">
                    Назад
                </button>
                <button
                    class="px-4 py-2 rounded text-white bg-orange-500 hover:bg-orange-600 disabled:opacity-50"
                    :disabled="!userInputs.name || isLoading"
                    @click="$emit('changeProduct', type, product?.id ?? null, userInputs)">
                    {{ type == "edit" ? "Изменить" : "Добавить" }}
                </button>
            </div>
        </div>
    </SlotModal>
</template>
<script lang="ts">
import { defineComponent, reactive, watch, type PropType } from "vue";
import { type IProduct } from "@/assets/interfaces/IProduct";
import SlotModal from "@/components/layout/SlotModal.vue";
import type { ProductForm } from "@/assets/interfaces/IProductForm.ts";

const emptyForm = (): ProductForm => ({ name: "", manufacturer: "", description: "" });

const productFormFields = [
    { name: "name", label: "Название" },
    { name: "manufacturer", label: "Производитель" },
    { name: "description", label: "Описание" },
] as const;

export default defineComponent({
    components: { SlotModal },
    props: {
        type: {
            type: String as PropType<"add" | "edit">,
        },
        product: {
            type: Object as PropType<IProduct>,
            default: null,
        },
        isLoading: {
            type: Boolean,
        },
        showModal: {
            type: Boolean,
            default: false,
        },
    },
    emits: ["closeModal", "changeProduct"],
    setup(props) {
        const userInputs = reactive<ProductForm>(emptyForm());

        watch(
            () => props.showModal,
            () => {
                if (!props.showModal) return;
                if (props.type == "edit" && props.product) {
                    userInputs.name = props.product.name ?? "";
                    userInputs.manufacturer = props.product.manufacturer ?? "";
                    userInputs.description = props.product.description ?? "";
                    userInputs.image = undefined;
                } else {
                    Object.assign(userInputs, emptyForm());
                }
            },
            { immediate: true },
        );

        const onFileChange = (event: Event) => {
            const input = event.target as HTMLInputElement;
            const file = input.files?.[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = () => {
                userInputs.image = String(reader.result ?? "");
            };
            reader.readAsDataURL(file);
        };

        return {
            userInputs,
            productFormFields,
            onFileChange,
        };
    },
});
</script>
