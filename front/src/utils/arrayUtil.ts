export const arraysEqual = (firstArr: unknown, secondArr: unknown): boolean => {
    if (Array.isArray(firstArr) && Array.isArray(secondArr)) {
        return JSON.stringify(firstArr) === JSON.stringify(secondArr);
    }
    return firstArr === secondArr;
}