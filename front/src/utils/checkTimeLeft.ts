export const checkTimeLeft = (dateTo: string) => {
    const formattedDate = new Date(dateTo.split('.').reverse().join('.')).getTime();
    const today = new Date().getTime();
    const timeLeft = formattedDate - today;

    if (timeLeft < 0) {
        return 'outdated';
    } else {
        console.log(timeLeft / 60 / 60 / 60 / 24);
        return timeLeft / 60 / 60 / 60 / 24;
    }
}