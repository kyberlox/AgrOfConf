import axios, { AxiosError, type AxiosProgressEvent, type AxiosRequestConfig } from 'axios';
import { handleApiErrors } from './apiStatusCodeErrors';
import type { IProduct } from '@/assets/interfaces/IProduct';
import type { IParameter } from '@/assets/interfaces/IParameter';

const VITE_API_URL = import.meta.env.VITE_API_URL;

const api = axios.create({
    baseURL: VITE_API_URL,
    withCredentials: false
})

// добавляю токен
// const authCookie = computed(() => useUserData().getAuthKey);
// const id = computed(() => useUserData().getMyId);

// api.interceptors.request.use((config) => {
//     config.headers.session_id = 'zalupa';
//     return config
// })
// vendorApi.interceptors.request.use((config) => {
//     config.headers.session_id = authCookie.value || '';
//     config.headers.user_id = id.value;
//     return config
// })

export default class Api {
    static async get(url: string, config?: AxiosRequestConfig, signal?: AbortSignal) {
        const mergedConfig: AxiosRequestConfig = { ...config, signal: signal ?? config?.signal }
        return await api.get(url, mergedConfig)
            .then(resp => resp.data)
            .catch(e => handleApiErrors(e))
    }

    static async post(url: string, data?: unknown, config?: AxiosRequestConfig & {
        onUploadProgress?: (progressEvent: AxiosProgressEvent) => void
    }, signal?: AbortSignal, needRespInfo = false
    ) {
        const mergedConfig: AxiosRequestConfig = { ...config, signal: signal ?? config?.signal }
        try {
            const respData = await api.post(url, data, mergedConfig)
            return needRespInfo ? respData : respData.data
        } catch (e) {
            console.error(e)
            handleApiErrors(e as AxiosError)
        }
    }

    static async put(url: string, data?: IProduct | IParameter[] | FormData | { name?: string, description?: string }) {
        return await api.put(url, data)
            .catch(e => handleApiErrors(e))
    }

    static async delete(url: string, data?: IProduct) {
        return await api.delete(url, { data })
            .catch(e => handleApiErrors(e))
    }
}