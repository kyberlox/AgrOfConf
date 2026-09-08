import Api from '@/utils/Api';

export const getProductFiles = async (id: string | number) => {
    const data = await Api.get(`/products/get_product_files/${id}`)
    return data
}