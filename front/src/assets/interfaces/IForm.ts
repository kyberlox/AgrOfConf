
export interface IFormattedData {
    all_values: string[],
    description: string | null,
    filtered_values?: string[],
    id: number,
    name: string,
    type?: string,
    required_type: string,
    response_value: string | Array<{ [key: string]: number }> | null,
    visibility: boolean
    editable?: boolean
    error?: string
    special?: boolean
    sort?: number
    is_validation?: boolean
} 

export interface IForm{
    matched_rows: number,
    parameters: IFormattedData[] ,
    product_id: number, 
    product_name: string,
    request_time: number
}