import Api from '@/utils/Api';
import { downloadFile } from '@/utils/downloadFile.ts';
import { toast } from 'vue3-toastify';
import type { userParams } from '@/assets/interfaces/IForm';
export const handleDownloadTkp = async (variantId: number, productId: number, userData: userParams) => {
    try {
        const response = await Api.post(`tkp_generation/create_tkp?file_id=${variantId}&product_id=${productId}&save_to_statistic=true`, userData, { responseType: 'blob' }, undefined, true);
        if (response) {
            const contentDisposition = response.headers['content-disposition'];
            const filename = contentDisposition?.split('filename=')[1].replaceAll('"', '');
            await downloadFile(response.data, filename)
        }
    }
    catch (error) {
        toast.error(error)
    }
}