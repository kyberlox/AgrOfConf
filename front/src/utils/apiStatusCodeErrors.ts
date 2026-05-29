import type { AxiosError } from "axios"
import { toast } from 'vue3-toastify';

export const handleApiErrors = (e: AxiosError) => {
    switch (e.status) {
        case 401:
             toast('Сессия истекла. Необходимо войти в систему заново.')
             break;
        case 404:
             toast('По запросу ничего не найдено')
             break;
        case 422:
             toast(e.status)
             break;
        case 502:
             toast('502')
             break;
        default:
            break;
    }
}