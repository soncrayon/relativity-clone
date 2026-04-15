import { useRef, useState } from "react";
import { useLoaderData, useRevalidator, Link } from "react-router";
import { Box, Button, Heading, Table, Badge, Text, HStack } from "@chakra-ui/react";
import type { Document, ProcessingStatus } from "@/features/documents/types";
import { uploadDocument, processDocument, chunkDocument } from "@/features/documents/api/documents";

const STATUS_COLOR: Record<ProcessingStatus, string> = {
  pending: "gray",
  processing: "blue",
  complete: "green",
  failed: "red",
};

const formatBytes = (bytes: number | null) => {
  if (bytes === null) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

export default function Documents() {
  const { documents, workspaceId } = useLoaderData() as {
    documents: Document[];
    workspaceId: number;
  };
  const revalidator = useRevalidator();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [uploading, setUploading] = useState(false);
  const [actionDocId, setActionDocId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUploadClick = () => fileInputRef.current?.click();

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await uploadDocument(workspaceId, file);
      revalidator.revalidate();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
      // Reset so the same file can be re-uploaded
      e.target.value = "";
    }
  };

  const handleProcess = async (docId: number) => {
    setActionDocId(docId);
    setError(null);
    try {
      await processDocument(workspaceId, docId);
      revalidator.revalidate();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Processing failed.");
    } finally {
      setActionDocId(null);
    }
  };

  const handleChunk = async (docId: number) => {
    setActionDocId(docId);
    setError(null);
    try {
      await chunkDocument(workspaceId, docId);
      revalidator.revalidate();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Chunking failed.");
    } finally {
      setActionDocId(null);
    }
  };

  return (
    <Box>
      <HStack justify="space-between" align="center" mb="6">
        <Heading size="xl">Documents</Heading>
        <HStack gap="3">
          <Button asChild variant="ghost" size="sm">
            <Link to="/workspaces">← Workspaces</Link>
          </Button>
          <Button
            size="sm"
            onClick={handleUploadClick}
            loading={uploading}
            loadingText="Uploading…"
          >
            Upload Document
          </Button>
        </HStack>
      </HStack>

      {/* Hidden file input — only accepts supported types */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,.txt,.eml"
        style={{ display: "none" }}
        onChange={handleFileChange}
      />

      {error && (
        <Text color="red.500" mb="4" fontSize="sm">
          {error}
        </Text>
      )}

      {documents.length === 0 ? (
        <Text color="gray.500">
          No documents yet. Upload a PDF, DOCX, TXT, or EML file to get started.
        </Text>
      ) : (
        <Table.Root size="md" variant="outline">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>Filename</Table.ColumnHeader>
              <Table.ColumnHeader>Type</Table.ColumnHeader>
              <Table.ColumnHeader>Size</Table.ColumnHeader>
              <Table.ColumnHeader>Status</Table.ColumnHeader>
              <Table.ColumnHeader>Actions</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {documents.map((doc) => (
              <Table.Row key={doc.id}>
                <Table.Cell fontFamily="mono" fontSize="sm">
                  {doc.filename}
                </Table.Cell>
                <Table.Cell>{doc.file_type.toUpperCase()}</Table.Cell>
                <Table.Cell>{formatBytes(doc.file_size)}</Table.Cell>
                <Table.Cell>
                  <Badge colorPalette={STATUS_COLOR[doc.processing_status]}>
                    {doc.processing_status}
                  </Badge>
                </Table.Cell>
                <Table.Cell>
                  <HStack gap="2">
                    {(doc.processing_status === "pending" ||
                      doc.processing_status === "failed") && (
                      <Button
                        size="xs"
                        variant="outline"
                        loading={actionDocId === doc.id}
                        loadingText="Processing…"
                        onClick={() => handleProcess(doc.id)}
                      >
                        Extract Text
                      </Button>
                    )}
                    {doc.processing_status === "complete" && (
                      <Button
                        size="xs"
                        variant="outline"
                        colorPalette="green"
                        loading={actionDocId === doc.id}
                        loadingText="Chunking…"
                        onClick={() => handleChunk(doc.id)}
                      >
                        Chunk
                      </Button>
                    )}
                  </HStack>
                </Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
      )}
    </Box>
  );
}
