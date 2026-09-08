<template>
<SlotModal>
    <div class="p-[40px] max-h-[90vh]">
        <span>Создание запроса</span>
        <div class="grid grid-cols-2 gap-[16px] mt-[16px]">
            <div v-for="(customerType, index) in costumersRef"
                 :key="'customer' + customerType.hidden + index"
                 class="p-[32px] rounded-[16px] border w-[500px] border-(--color-information-gray-200)"
                 :class="{ 'border-transparent': customerType.hidden }">
                <div v-if="!customerType.hidden"
                     class="font-semibold">
                    {{ customerType.title }}
                </div>
                <div class="flex flex-col gap-[8px] mt-[24px]">
                    <BaseButton v-if="customerType.hidden"
                                @clicked="customerType.hidden = false">
                        <div class="flex flex-row items-center gap-[4px] hover:text-[#6B778C] duration-[0.2s]">
                            <AddOrgIcon class="text-[#6B778C]" />
                            <span>{{ customerType.title }}</span>
                        </div>
                    </BaseButton>
                    <div v-else
                         v-for="(question, index) in customerType.title == 'Запрос' ? requestFields : customerFields"
                         :key="index + 'reqquestion'">
                        <div v-if="question.title == 'Срок'"
                             class="flex flex-row gap-[8px]">
                            Срок ТКП
                            <input type="date" />
                            Срок поставки
                            <input type="date" />
                        </div>
                        <div v-else-if="!customerType.hidden">
                            <BaseInput v-if="question.type == 'input'"
                                       :inputSettings="initInputProps(customerType.title, question.title, index)" />
                            <BaseSelect v-else-if="question.type == 'select'"
                                        :selectSettings="initSelectProps(question.title, customerType, index)" />
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="max-w-fit ml-auto mt-[16px] pb-[16px]">
            <BaseButton :buttonSettings="{ class: 'button-primary', }">
                Создать
            </BaseButton>
        </div>
    </div>
</SlotModal>
</template>
<script lang='ts'>
import { defineComponent, ref } from 'vue';
import SlotModal from '@/components/layout/SlotModal.vue';
import { BaseInput, BaseButton, BaseSelect } from 'beans-ui-kit';
import AddOrgIcon from '@/assets/icons/AddOrg.svg?component';
import { requestFields, customers, customerFields } from './createRequestData';

export default defineComponent({
    components: {
        SlotModal,
        BaseInput,
        BaseButton,
        BaseSelect,
        AddOrgIcon
    },
    props: {},
    setup() {
        const costumersRef = ref(customers);
        const initInputProps = (customerType: string, question: string, index: number) => {
            return {
                class: 'input-form',
                type: 'text',
                name: question + customerType + (index + 1),
                label: question,
            }
        }

        const initSelectProps = (question: string, customerType: { title: string, options: Array<string> }, index: string) => {
            console.log(customerType)
            return {
                id: 'formReq' + index,
                placeholder: '...',
                class: 'input-form',
                label: question,
                options: 'option' in customerType ? customerType.options : []
            }
        }

        console.log(customerFields)

        return {
            costumersRef,
            requestFields,
            customerFields,
            initSelectProps,
            initInputProps,
        }
    }
});
</script>