export interface IRequestsData {
    requestsData: {
        ko: { id: number, name: string, users: { id: number, fio: string, avatar: string }[] }[],
    },
    isAdmin: boolean
}

export interface IUserEntity {
    id: number,
    LAST_NAME: string,
    NAME: string,
    SECOND_NAME: string
    PERSONAL_PHOTO: string
    PERSONAL_BIRTHDAY: string
    PERSONAL_CITY: string
    WORK_POSITION: string
    UF_DEPARTMENT: string[]
    Direction: string[]
    UF_PHONE_INNER: string
    EMAIL: string
    UF_USR_1586854037086: string
}