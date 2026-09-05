import Api from '@/utils/Api';

export const getTkpVariants = async (id: string | number) => {
    const data = await Api.get(`/tkp_generation/get_tkp_of_product/${id}`)
    return data
}