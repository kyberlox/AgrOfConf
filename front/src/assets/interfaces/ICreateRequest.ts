export interface IRequestCostumerData {
    id: string;
    title: string;
    type: string;
    options?: Array<string>;
}

export interface ICustomer {
    title: string;
    id: string;
    hidden: boolean;
}

export interface IRequest {
    request: {
        request_purpose: string;
        description: string;
        construction_project: string;
        tkp_term: string;
        delivery_time: string;
        procedure_type: string;
    };
    customer: {
        id?:
            | number
            | {
                  organization: string;
                  address: string;
                  telephone: string;
                  email: string;
                  inn: string;
                  registered_address: string;
                  international_address: string;
                  website: string;
                  customer_type: string;
                  additional_information: string;
                  contacts: [
                      {
                          full_name: string;
                          job_title: string;
                          work_phone: string;
                          mobile_phone: string;
                          email: string;
                          visibility: true;
                          field_of_view: {
                              additionalProp1: {};
                          };
                      },
                  ];
              };
    };
    organization: {
        id?:
            | 0
            | {
                  organization: string;
                  address: string;
                  telephone: string;
                  email: string;
                  inn: string;
                  registered_address: string;
                  international_address: string;
                  website: string;
                  customer_type: string;
                  additional_information: string;
                  contacts: [
                      {
                          full_name: string;
                          job_title: string;
                          work_phone: string;
                          mobile_phone: string;
                          email: string;
                          visibility: true;
                          field_of_view: {
                              additionalProp1: {};
                          };
                      },
                  ];
              };
    };
    end_customer: {
        id:
            | number
            | {
                  organization: string;
                  address: string;
                  telephone: string;
                  email: string;
                  inn: string;
                  registered_address: string;
                  international_address: string;
                  website: string;
                  customer_type: string;
                  additional_information: string;
                  contacts: [
                      {
                          full_name: string;
                          job_title: string;
                          work_phone: string;
                          mobile_phone: string;
                          email: string;
                          visibility: true;
                          field_of_view: {
                              additionalProp1: {};
                          };
                      },
                  ];
              };
    };
}

export type CreateRequestType = DeepPartial<IRequest>;

export type DeepPartial<T> = T extends undefined
    ? {}
    : { [key in keyof T]?: T[key] extends "object" ? DeepPartial<T[key]> : T[key] };
