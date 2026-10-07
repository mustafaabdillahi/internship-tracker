import type { Application } from "./application";

export interface StageEvent {
    id: number;
    stage: string;
    created_at: string;
}

export interface ApplicationEmail {
    id: number;
    subject: string | null;
    sender: string | null;
    received_at: string;
    html_body: string | null;
    text_body: string | null;
}

export interface ApplicationNote {
    id: string;
    content: string;
    created_at: string;
}

export interface ApplicationDeadline {
    id: string;
    deadline_type: string;
    description: string | null;
    due_at: string;
}

export interface ApplicationDetail {
    application: Application;
    stage_events: StageEvent[];
    emails: ApplicationEmail[];
    notes: ApplicationNote[];
    deadlines: ApplicationDeadline[];
}