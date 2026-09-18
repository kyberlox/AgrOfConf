export interface IParameter {
  name: string
  description: string | null
  type: string
  measuring_unit: string | null
  visibility: boolean
  editable: boolean
  required_type: 'list' | 'user_input' | 'select-input' | 'checkbox' | 'drawing'
  table_name: string | null
  field_of_view: string | null
  id: number
  sort: number
  // Новая система формул: { func: "count_A", validate: "validate_nonzero", type: "formula" }
  formula_config?: Record<string, unknown>
  special?: boolean
}
