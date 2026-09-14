import type { AxiosError } from "axios"
import { toast } from 'vue3-toastify';
import router from '@/router';

export const handleApiErrors = (e: AxiosError) => {
     switch (e.status) {
          case 400:
               return toast.error('Некорректные данные');
          case 401:
               toast.error('Сессия истекла. Необходимо войти в систему заново.')
               return router.push({ name: 'login' })
          case 404:
               return toast.error('По запросу ничего не найдено');
          case 422:
               return toast.error(e.status);
          case 500:
               return toast.error('Ошибка сервера, сообщите в поддержку сайта');
          case 502:
               return toast.error('502');
          default:
               break;
     }
}