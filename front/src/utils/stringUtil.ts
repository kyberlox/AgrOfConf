export const upFirstLetter = (text: string) => {
    const startArray = Array.from(text);
    const target = startArray[0]?.toUpperCase();
    if (!target) return;
    startArray[0] = target;
    return startArray.join("");
};
