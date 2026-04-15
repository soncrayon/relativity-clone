import type { LoaderFunctionArgs } from "react-router";
import { getDocuments } from "@/features/documents/api/documents";

export const loader = async ({ params }: LoaderFunctionArgs) => {
  const workspaceId = Number(params.workspaceId);
  const documents = await getDocuments(workspaceId);
  return { documents, workspaceId };
};
