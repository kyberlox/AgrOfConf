<template>
    <TransitionGroup name="fade-form" tag="div" class="grid gap-[16px] py-[16px]" :class="`grid-cols-${openCustomers}`">
        <div v-for="(customerType, index) in costumersRef?.filter((e) => !e.hidden)" :key="'customer' + index">
            <div
                class="p-[32px] max-w-full rounded-[16px] border w-full border-(--color-information-gray-200)"
                :class="{ 'border-transparent': customerType.hidden }">
                <div class="font-semibold">
                    {{ customerType.title }}
                </div>
                <div class="flex flex-col gap-[8px] mt-[24px]">
                    <div
                        v-for="(question, index) in customerType.title == 'Запрос' ? requestFields : customerFields"
                        :key="index + 'reqquestion'">
                        <BaseInput
                            v-if="question.type == 'input'"
                            @valueChanged="
                                (value: string) => setFormAnswer(customerType.id as keyof IRequest, question.id, value)
                            "
                            :inputSettings="initInputProps(customerType.title, question.title, index)" />
                        <div v-else-if="question.type == 'date'" class="input-form__wrapper" :key="index + 'dateType'">
                            <div class="input-form__label">
                                {{ question.title }}
                            </div>
                            <div class="input-form">
                                <DatePicker
                                    @newDate="
                                        (date: Date) =>
                                            setFormAnswer(customerType.id as keyof IRequest, String(question.id), date)
                                    " />
                            </div>
                        </div>
                        <BaseSelect
                            v-else-if="question.type == 'select' && 'options' in question"
                            @valueChanged="
                                (value: string) =>
                                    setFormAnswer(customerType.id as keyof IRequest, String(question.id), value)
                            "
                            :selectSettings="initSelectProps(question.title, question, String(index))" />
                        <BaseTextarea
                            v-else-if="question.type == 'textarea'"
                            :textareaSettings="initTextAreaProps(question.title, question.title, String(index))" />
                    </div>
                </div>
            </div>
        </div>
    </TransitionGroup>
</template>
<script lang="ts">
import { defineComponent, type PropType } from "vue";
import type { IRequestCostumerData, IRequest, ICustomer } from "@/assets/interfaces/ICreateRequest";
import { format } from "@/utils/dateUtil";
import { requestFields, customerFields } from "@/assets/static/createRequestData";
import { BaseInput, BaseSelect, BaseTextarea } from "beans-ui-kit";
import DatePicker from "@/components/layout/DatePicker.vue";

export default defineComponent({
    components: { BaseSelect, BaseInput, DatePicker, BaseTextarea },
    props: {
        reqSending: {
            type: Boolean,
        },
        openCustomers: {
            type: Number,
        },
        costumersRef: {
            type: Array as PropType<ICustomer[]>,
        },
    },
    emits: ["formAnswerChange"],
    setup(props, { emit }) {
        const initInputProps = (title: string, question: string, index: number) => {
            return {
                class: "input-form",
                type: "text",
                name: question + title + (index + 1),
                label: question,
                disabled: props.reqSending,
                placeholder: "...",
            };
        };

        const initTextAreaProps = (title: string, question: string, index: string) => {
            return {
                class: "input-form",
                name: question + title + (index + 1),
                label: question,
                disabled: props.reqSending,
                placeholder: "...",
            };
        };

        const initSelectProps = (question: string, item: IRequestCostumerData, index: string) => {
            return {
                id: "formReq" + index,
                placeholder: "...",
                class: "input-form",
                label: question,
                options: "options" in item ? item.options : [],
                disabled: props.reqSending,
            };
        };

        const setFormAnswer = (customerType: string, questionId: string, value: Date | string) => {
            if (!value && value !== "") return;
            emit("formAnswerChange", customerType, questionId, value instanceof Date ? format(value) : value);
        };

        return {
            requestFields,
            customerFields,
            initInputProps,
            initSelectProps,
            initTextAreaProps,
            setFormAnswer,
            format,
        };
    },
});
</script>
