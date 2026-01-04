const ACCESS_KEY = "jt_access";
const REFRESH_KEY = "jt_refresh";

export const tokenStorage = {
    getAccess (): string | null {
        return localStorage.getItem(ACCESS_KEY);
    },
    setAccess (token: string): void {
        localStorage.setItem(ACCESS_KEY, token);
    },
    getRefresh (): string | null {
        return localStorage.getItem(REFRESH_KEY);
    },
    setRefresh (token: string): void {
        localStorage.setItem(REFRESH_KEY, token);
    },
    clear (): void {
        localStorage.removeItem(ACCESS_KEY);
        localStorage.removeItem(REFRESH_KEY);
    }
};