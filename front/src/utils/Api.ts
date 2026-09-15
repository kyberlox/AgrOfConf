import axios, { AxiosError, type AxiosProgressEvent, type AxiosRequestConfig } from 'axios';
import { handleApiErrors } from '../composables/apiStatusCodeErrors';
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
if (import.meta.env.DEV) {
    api.interceptors.request.use((config) => {
        config.headers.session_id = '0ab5bdba-8e3c-4743-bc3e-9fb275fe8b8e';
        return config
    })
}

// vendorApi.interceptors.request.use((config) => {
//     config.headers.session_id = authCookie.value || '';
//     config.headers.user_id = id.value;
//     return config
// })

export default class Api {
    static async get(url: string, config?: AxiosRequestConfig, signal?: AbortSignal) {
        const mergedConfig: AxiosRequestConfig = { ...config, signal: signal ?? config?.signal }
        try {
            const request = await api.get(url, mergedConfig)
            return request?.data
        } catch (error) {
            return handleApiErrors(error as AxiosError)
        }
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
            if ((e as Error).name == 'CanceledError')
                return
            else
                handleApiErrors(e as AxiosError)
        }
    }

    static async put(url: string, data?: IProduct | IParameter[] | FormData | Record<string, unknown>) {
        try {
            return await api.put(url, data);
        }
        catch (error) {
            handleApiErrors(error as AxiosError)
        }
    }

    static async delete(url: string, data?: IProduct) {
        try {
            return await api.delete(url, { data })
        }
        catch (error) {
            handleApiErrors(error as AxiosError)
        }
    }
}