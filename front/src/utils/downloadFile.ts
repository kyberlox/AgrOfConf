export const downloadFile = async (docData: Blob, fileName: string) => {
    try {
        const url = globalThis.URL.createObjectURL(docData);
        const link = globalThis.document.createElement('a');
        link.href = url;
        link.download = fileName;
        globalThis.document.body.appendChild(link);
        link.click();
        globalThis.document.body.removeChild(link);
        globalThis.URL.revokeObjectURL(url)
    }
    catch (error) {
        console.error(error)
    }
}