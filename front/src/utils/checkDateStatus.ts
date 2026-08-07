export const checkDateStatus = (date1: string) => {
    const formattedDate = date1.split('.').reverse().join('.');
    const today = new Date();
    const utilDate = new Date();
    const twentyDaysRoof = utilDate.setDate(new Date().getDate() + 20);
    if (new Date(formattedDate).getTime() >= today.getTime()) {
        if (new Date(formattedDate).getTime() <= twentyDaysRoof) {
            return 'warning'
        }
        return 'actual'
    }
    else if (new Date(formattedDate).getTime() < today.getTime()) {
        return 'outdated'
    } else
        return 'unknown'
}