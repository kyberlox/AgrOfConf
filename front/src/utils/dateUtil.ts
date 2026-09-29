export const format = (dateToFormat: Date) => {
    const day = String(dateToFormat.getDate()).padStart(2, "0");
    const month = String(dateToFormat.getMonth() + 1).padStart(2, "0");
    const year = dateToFormat.getFullYear();
    return `${day}.${month}.${year}`;
};
