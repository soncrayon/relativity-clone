export type ProcessingStatus = "pending" | "processing" | "complete" | "failed";

export interface Document {
  id: number;
  filename: string;
  file_type: string;
  file_size: number | null;
  processing_status: ProcessingStatus;
  created_at: string;
}
