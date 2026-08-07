export const replaceSpotOrComma = (item: string | null, toReplace: 'spot' | 'comma') => {
    if (!item) return null
    else
        if (!item.match(/^\d+([.,]\d+)?$/)) {
            return item
        }
        else {
            return toReplace == 'spot' ? item.replace('.', ',') : item.replace(',', '.')
        }
}