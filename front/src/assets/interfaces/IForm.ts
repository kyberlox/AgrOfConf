
export interface IFormattedData {
    all_values: string[],
    description: string | null,
    filtered_values?: string[],
    id: number,
    name: string,
    required_type: string,
    response_value: string | null,
    visibility: boolean
    error?: string
} 

export interface IForm{
    matched_rows: number,
    parameters: IFormattedData[] ,
    product_id: number, 
    product_name: string,
    request_time: number
}