import Api from '@/utils/Api';
import { downloadFile } from '@/utils/downloadFile.ts';
import { toast } from 'vue3-toastify';
type userDataType = { [key: string]: string | boolean | Array<{ [key: string]: number }> }

export const handleDownloadTkp = async (variantId: number, productId: number, userData: userDataType) => {
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