export const copyFormData = (formDataToCopy: FormData) => {
    const newformData = new FormData();
    for (let [key, value] of formDataToCopy.entries()) {
        newformData.append(key, value)
    }
    return newformData
}