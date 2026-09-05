// Число с дробной частью и возможной научной нотацией (например 1.897032904e-05).
const DECIMAL_RE = /^[-+]?\d+([.,]\d+)?([eE][-+]?\d+)?$/

export const replaceSpotOrComma = (item: string | number | null | undefined, toReplace: 'spot' | 'comma') => {
    // Значение может прийти числом (например, результат формулы 78.5398).
    // Приводим к строке, чтобы не падать на .match().
    if (item === null || item === undefined || item === '') return null
    const text = String(item)

    // Меняем разделитель только у «числовых» значений (в т.ч. научная нотация),
    // чтобы случайно не портить обычные строки. Остальное возвращаем как есть.
    if (!text.match(DECIMAL_RE)) {
        return text
    }
    else {
        return toReplace == 'spot' ? text.replace('.', ',') : text.replace(',', '.')
    }
}