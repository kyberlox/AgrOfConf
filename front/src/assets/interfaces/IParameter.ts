export interface IParameter {
    name: string,
    description: string,
    type: string,
    measuring_unit: string,
    visibility: boolean,
    editable: boolean,
    required_type: 'list' | 'userInput',
    table_name: string,
    field_of_view: string,
    id: number,
    sort: number | boolean
    // Новая система формул: { func: "count_A", validate: "validate_nonzero", type: "formula" }
    formula_config?: Record<string, unknown>
}