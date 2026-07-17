import type { AxiosError } from "axios"
import { toast } from 'vue3-toastify';

export const handleApiErrors = (e: AxiosError) => {
     switch (e.status) {
          case 400:
               return toast.error('Некорректные данные');
          case 401:
               return toast.error('Сессия истекла. Необходимо войти в систему заново.');
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