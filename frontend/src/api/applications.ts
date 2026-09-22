import type { Application, ApplicationStage } from "../types/application";
import apiClient from "./client";

export async function getApplications(): Promise<Application[]> {
    const response = await apiClient.get<Application[]>("/applications");
    return response.data;
}

export async function getApplication(id: string) {
    const response = await apiClient.get(`/applications/${id}`);
    return response.data;
}

export async function updateApplicationStage(id: number, stage: ApplicationStage): Promise<Application> {
    const response = await apiClient.patch<Application>(
        `/applications/${id}`,
        { stage }
    );
    return response.data;
}