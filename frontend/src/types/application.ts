export const applicationStages = [
  "applied",
  "oa",
  "interview",
  "offer",
  "rejected",
  "withdrawn"
] as const;

export type ApplicationStage = (typeof applicationStages)[number];

export interface Application {
  id: number;
  company_name: string | null;
  role: string | null;
  stage: ApplicationStage | null;
  date_applied: string;
  loc: string | null;
  employment_type: string | null;
  notes: string | null;
}

export interface ApplicationFormData {
  company_name: string;
  stage: ApplicationStage;
  role: string | null;
  loc: string | null;
  employment_type: string | null;
  notes: string | null;
}