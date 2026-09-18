import { onMounted, ref } from 'vue'
import Api from '@/utils/Api'

interface FormulaFunctionsResponse {
  algorithms?: string[]
  validators?: string[]
}

export const useFormulaFunctions = () => {
  const algorithms = ref<string[]>([])
  const validators = ref<string[]>([])

  const loadFormulaFunctions = async () => {
    try {
      const data = (await Api.get('formula_functions')) as FormulaFunctionsResponse | undefined
      algorithms.value = data?.algorithms ?? []
      validators.value = data?.validators ?? []
    } catch (error) {
      console.error('Не удалось получить список функций:', error)
    }
  }

  onMounted(loadFormulaFunctions)

  return {
    algorithms,
    validators,
    loadFormulaFunctions,
  }
}
