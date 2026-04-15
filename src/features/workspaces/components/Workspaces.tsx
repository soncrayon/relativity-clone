import { useLoaderData } from "react-router";
import { Link } from "react-router";
import { Box, Heading, Table, Button } from "@chakra-ui/react";
import type { Workspace } from "@/features/workspaces/types";

export default function Workspaces() {
  const { workspaces } = useLoaderData() as { workspaces: Workspace[] };

  return (
    <Box>
      <Heading size="xl" mb="6">
        Workspaces
      </Heading>
      <Table.Root size="md" variant="outline">
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader>ID</Table.ColumnHeader>
            <Table.ColumnHeader>Name</Table.ColumnHeader>
            <Table.ColumnHeader>Description</Table.ColumnHeader>
            <Table.ColumnHeader></Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {workspaces.map((ws) => (
            <Table.Row key={ws.id}>
              <Table.Cell>{ws.id}</Table.Cell>
              <Table.Cell>{ws.name}</Table.Cell>
              <Table.Cell>{ws.description}</Table.Cell>
              <Table.Cell>
                <Button asChild size="xs" variant="outline">
                  <Link to={`/workspaces/${ws.id}/documents`}>Documents →</Link>
                </Button>
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
    </Box>
  );
}
