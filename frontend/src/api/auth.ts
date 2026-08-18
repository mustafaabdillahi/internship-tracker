import apiClient from "./client";

export interface User {
    id: string;
    firstname: string;
    surname: string;
    email: string;
}

export async function getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>("/auth/me");
    return response.data;
}