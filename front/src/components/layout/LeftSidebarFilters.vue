<template>
<div class="flex flex-col gap-[4px] mt-[4px] pb-[12px]">
    <BaseSelect v-for="(item, index) in tabs"
                :key="'leftSideNav' + index"
                :propsLabel="item.title"
                :props-options="['1', '2']"
                :props-placeholder="''"
                :propsClass="'sidebar__filter'"
                :props-id="'sidebar__filter' + index"
                @value-changed="(value) => handleFilterChange(value, item.name)" />
</div>
</template>
<script lang='ts'>
import { BaseSelect } from 'beans-ui-kit';
import { defineComponent, ref, type Ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';

export default defineComponent({
    components: { BaseSelect },
    props: {
        tabs: Array<{ name: string, title: string }>,
        link: {
            type: String
        }
    },
    setup(props) {
        const filtersQuery = ref({}) as Ref<{ key: string, value: string }>;
        const router = useRouter();

        const handleFilterChange = (value: string, key: string) => {
            console.log(filtersQuery.value);

            filtersQuery.value[key as keyof typeof filtersQuery.value] = value;
            // router.push({ name: props.link, query: { [key]: value } })
            router.push({ name: props.link, query: filtersQuery.value })
        }

        return {
            handleFilterChange
        }
    }
});
</script>
<style>
.sidebar__filter__wrapper {
    max-width: 100%;
    padding-left: 40px;
    padding-right: 12px;
    display: flex;
    flex-direction: column;
    font-weight: 500;
    font-size: 14px;
}

.sidebar__filter {
    width: 100%;
    padding-left: 12px;
    padding-right: 4px;
    padding-block: 10px;
    border-radius: 8px;
    background-color: white;
    border: 1px solid transparent;
    transition-duration: 300ms;
    transform: transition;
    outline: none;
}

.sidebar__filter:hover {
    border: 1px solid #F36E3C;
    cursor: pointer;
}
</style>