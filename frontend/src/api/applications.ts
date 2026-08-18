import apiClient from "./client";

export async function getApplications() {
    const response = await apiClient.get("/applications");
    return response.data;
}

export async function getApplication(id: string) {
    const response = await apiClient.get(`/applications/${id}`);
    return response.data;
}