export interface IParameter{
    name: string,
    description: string,
    type: string,
    measuring_unit: string,
    visibility: boolean,
    required_type: 'list' | 'userInput',
    table_name: string,
    field_of_view: string,
    id: number,
    sort: number | boolean
}