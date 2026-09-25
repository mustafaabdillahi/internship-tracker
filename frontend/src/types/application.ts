export type ApplicationStage = 
  | "applied"
  | "oa"
  | "interview"
  | "offer"
  | "rejected"
  | "withdrawn";

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