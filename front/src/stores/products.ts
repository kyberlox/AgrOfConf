import { defineStore } from "pinia";
import type { IProduct } from "@/assets/interfaces/IProduct";

export const useProductsData = defineStore('productsData', {
    state: () => ({
        products: [] as IProduct[],
    }),

    actions: {
        setProducts(products: IProduct[]) {
            this.products = products;
        }
    },

    getters: {
        getProducts: (state) => state.products,
    }
});
