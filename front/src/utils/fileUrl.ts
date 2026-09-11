/**
 * Нормализует путь к статическому файлу для корректной отдачи через Nginx.
 *
 * Файлы физически раздаются FastAPI по `/api/files/...`, но в БД исторически
 * сохраняются как `/files/...`. Без префикса `/api` такой путь уходит на SPA-роутер
 * фронтенда и возвращает HTML вместо картинки.
 */
export const fileUrl = (url?: string | null): string => {
    if (!url) return '';
    if (url.startsWith('/files/')) return '/api' + url;
    return url;
};