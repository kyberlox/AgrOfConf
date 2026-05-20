export interface IUserData {
    fio: string,
    position: string,
    avatar: string,
    requestsData: {
        ko: {id: number, name: string, users: {id: number, fio: string, avatar: string}[]}[],
    }, 
    isAdmin: boolean
}