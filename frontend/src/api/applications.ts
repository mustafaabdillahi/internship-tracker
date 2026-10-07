import type { Application, Filters, ApplicationFormData } from "../types/application";
import apiClient from "./client";

export async function getApplications(
    filters?: Filters
): Promise<Application[]> {
    const params = new URLSearchParams();

    if (filters?.company) {
        params.set("company", filters.company);
    }
    if (filters?.location) {
        params.set("location", filters.location);
    }
    if (filters?.role) {
        params.set("role", filters.role);
    }
    if (filters?.dateFrom) {
        params.set("date_from", filters.dateFrom);
    }
    if (filters?.dateTo) {
        params.set("date_to", filters.dateTo);
    }

    const response = await apiClient.get<Application[]>(`/applications?${params.toString()}`);
    return response.data;
}

export async function getApplicationDetails(id: number) {
    const response = await apiClient.get(`/applications/detail/${id}`);
    return response.data;
}

export async function getApplication(id: number) {
    const response = await apiClient.get(`/applications/${id}`);
    return response.data;
}

export async function createApplication(data: ApplicationFormData): Promise<Application> {
    const response = await apiClient.post<Application>(
        `/application/create`,
        data
    );

    return response.data;
}

export async function updateApplication(id: number, data: Partial<ApplicationFormData>): Promise<Application> {
    const response = await apiClient.patch<Application>(
        `/application/update/${id}`,
        data
    );

    return response.data;
}

export async function deleteApplication(id: number) {
    const response = await apiClient.delete(`/application/delete/${id}`);
    return response.data;
}