<template>
    <div
        class="flex flex-col gap-2 mt-4 border border-gray-200 p-[20px] rounded-xl bg-gray-50"
        v-if="Object.keys(systemPrompt).length">
        <h3 class="text-lg font-medium mb-2">Системный промпт</h3>
        <div v-for="item in ['validation_prompt', 'unified_prompt']" :key="item">
            <span>{{ ruPromptNames[item as keyof typeof ruPromptNames] }}</span>
            <BaseTextarea
                class="mt-[10px]"
                :textarea-settings="
                    initTextareaProps(item, String(systemPrompt[item as keyof typeof systemPrompt]) || '')
                "
                @value-changed="(val) => (systemPrompt[item as keyof typeof systemPrompt] = val)" />
        </div>
        <span>Значения по умолчанию</span>
        <div v-if="systemPrompt.rules_table?.length" class="bg-white">
            <div class="grid grid-cols-4 gap-[20px] p-[15px]">
                <div v-for="(rule, index) in systemPrompt.rules_table" :key="'rule' + index">
                    <div class="flex flex-row item-center justify-center content-center gap-[5px]">
                        <BaseInput
                            :inputSettings="initInputSettings(rule, index)"
                            @valueChanged="(value: string) => handleValueChanged(rule.name, value)" />
                        <div
                            class="text-sm mb-auto bg-red-500 rounded-md w-[25px] text-center text-white hover:bg-red-600 cursor-pointer"
                            @click="deleteRule(rule.name)">
                            X
                        </div>
                    </div>
                </div>
                <div class="py-[20px]">
                    <BaseButton :button-settings="{ class: 'button-secondary' }" @clicked="showParamsModal = true">
                        Добавить
                    </BaseButton>
                </div>
            </div>
        </div>
        <BaseButton
            class="mt-[12px] flex flex-row items-center max-w-fit"
            :buttonSettings="{ class: 'button-primary', disabled: promptIsLoading }"
            @clicked="saveNewPrompt">
            <span v-if="!promptIsLoading">Подтвердить</span>
            <Loader class="max-w-fit" v-else />
        </BaseButton>

        <SlotModal v-if="showParamsModal" @closeModal="showParamsModal = false">
            <div class="max-h-[500px] overflow-y-auto flex flex-col gap-[10px]">
                <div
                    v-for="(item, index) in params"
                    :key="'promptParam' + index"
                    class="border border-b border-gray-300 p-[5px] rounded-[10px]"
                    @click="setRule(item.name)">
                    {{ item.name }}
                </div>
            </div>
        </SlotModal>
    </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, ref, type PropType } from "vue";
import { BaseButton, BaseTextarea, BaseInput } from "beans-ui-kit";
import Api from "@/utils/Api";
import SlotModal from "@/components/layout/SlotModal.vue";
import { type IParameter } from "@/assets/interfaces/IParameter";
import Loader from "@/components/layout/Loader.vue";

interface ISystemPrompt {
    product_id?: number;
    validation_prompt?: string;
    unified_prompt?: string;
    rules_table?: { name: string; default: string }[];
}

export default defineComponent({
    components: { BaseTextarea, BaseButton, BaseInput, SlotModal, Loader },
    props: {
        id: {
            type: Number,
        },
        params: {
            type: Array<IParameter>,
        },
    },
    setup(props) {
        const systemPrompt = ref<ISystemPrompt>({});
        const promptIsLoading = ref(false);
        const showParamsModal = ref(false);

        const ruPromptNames = {
            validation_prompt: "Промпт первого слоя",
            unified_prompt: "Промпт второго слоя",
        };

        onMounted(async () => {
            systemPrompt.value = await Api.get(`/AI/get_product_prompt/${props.id}`);
        });

        const initTextareaProps = (name: string, value: string) => {
            return {
                class: "textarea-admin",
                value: value,
                name: name,
                placeholder: "Введите системный промпт",
                disabled: false,
            };
        };

        const initInputSettings = (param: { name: string; default: string }, index: number | string) => {
            return {
                class: "input-param--no-group",
                placeholder: "Впишите значение",
                value: param.default,
                name: param.name + (Number(index) + 1),
                label: param.name,
                disabled: promptIsLoading.value,
            };
        };

        const saveNewPrompt = async () => {
            try {
                promptIsLoading.value = true;
                const data = await Api.post(`/AI/save_product_prompt/${props.id}`, systemPrompt.value);
            } finally {
                promptIsLoading.value = false;
            }
        };

        const setRule = (item: string) => {
            systemPrompt.value.rules_table?.push({ name: item, default: "" });
            showParamsModal.value = false;
        };

        const deleteRule = (item: string) => {
            systemPrompt.value.rules_table = systemPrompt.value.rules_table?.filter((e) => e.name !== item);
        };

        const handleValueChanged = (name: string, value: string) => {
            if (value == undefined) return;
            const target = systemPrompt.value.rules_table?.find((e) => e.name == name);
            if (target) target.default = value;
        };

        return {
            systemPrompt,
            ruPromptNames,
            showParamsModal,
            promptIsLoading,
            deleteRule,
            setRule,
            handleValueChanged,
            saveNewPrompt,
            initTextareaProps,
            initInputSettings,
        };
    },
});
</script>

<style>
.textarea-admin {
    width: 100%;
    padding: 15px;
    border: 1px solid rgba(81, 80, 80, 0.232);
    outline: none;
    background: white;
    border-radius: 5px;
    height: 500px;
}
</style>
