<template>
    <SlotModal @closeModal="$emit('closeModal')">
        <div class="py-[16px] px-[22px] max-h-[90vh]">
            <div class="flex flex-row items-center justify-between gap-[20px]">
                <BaseButton
                    :buttonSettings="{ class: 'button-primary', disabled: reqSending }"
                    @clicked="createRequest">
                    Создать запрос
                </BaseButton>
                <div class="flex flex-row gap-[20px]">
                    <template v-for="fieldType in ['organization', 'end_customer']" :key="fieldType + 'btn'">
                        <BaseButton
                            v-if="costumersRef.find((e) => e.id == fieldType)?.hidden"
                            @clicked="costumerButtonClick(fieldType)">
                            <div class="flex flex-row items-center gap-[4px] hover:text-[#6B778C] duration-[0.2s]">
                                <AddOrgIcon class="text-[#6B778C]" />
                                <span>{{ costumersRef.find((e) => e.id == fieldType)?.title || "" }}</span>
                            </div>
                        </BaseButton>
                    </template>
                </div>
            </div>
            <FormGrid :openCustomers="openCustomers" :costumersRef="costumersRef" @formAnswerChange="setFormAnswer" />
        </div>
    </SlotModal>
</template>
<script lang="ts">
import { defineComponent, ref, computed } from "vue";
import SlotModal from "@/components/layout/SlotModal.vue";
import { BaseButton } from "beans-ui-kit";
import AddOrgIcon from "@/assets/icons/AddOrg.svg?component";
import { customers } from "@/assets/static/createRequestData";
import type { CreateRequestType } from "@/assets/interfaces/ICreateRequest.ts";
import Api from "@/utils/Api";
import FormGrid from "./FormGrid.vue";
import { emit } from "process";

export default defineComponent({
    components: {
        SlotModal,
        BaseButton,
        AddOrgIcon,
        FormGrid,
    },
    emits: ["closeModal", "goToReq"],
    props: {},
    setup(_, { emit }) {
        const costumersRef = ref(customers);
        const form = ref<CreateRequestType>({});
        const reqSending = ref(false);

        const setFormAnswer = <K extends keyof CreateRequestType, P extends keyof CreateRequestType[K]>(
            formType: K,
            key: P,
            value: unknown,
        ) => {
            let section = form.value[formType] as Record<string, unknown>;
            if (!section) {
                section = {};
                form.value[formType] = section as CreateRequestType[K];
            }
            section[key as keyof typeof section] = value;
        };

        const createRequest = async () => {
            try {
                reqSending.value = true;
                const sendReq = await Api.post("/requests/", form.value);
                if (!sendReq) return;
                emit("goToReq", sendReq.id);
                emit("closeModal");
            } finally {
                reqSending.value = false;
            }
        };

        const costumerButtonClick = (fieldType: string) => {
            const target = costumersRef.value.find((e) => e.id == (fieldType as keyof typeof e.id));
            if (target) target.hidden = false;
        };

        return {
            costumersRef,
            reqSending,
            openCustomers: computed(() => costumersRef.value.filter((e) => !e.hidden).length),
            costumerButtonClick,
            setFormAnswer,
            createRequest,
        };
    },
});
</script>
