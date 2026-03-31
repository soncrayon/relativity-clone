
import { useLoaderData } from 'react-router';
import { Box, Heading, Table } from '@chakra-ui/react';
import type { Group } from '@/data/groups';

export default function Groups() {
  const { groups } = useLoaderData() as { groups: Group[] };

  return (
    <Box>
      <Heading size="xl" mb="6">Groups</Heading>
      <Table.Root size="md" variant="outline">
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader>ID</Table.ColumnHeader>
            <Table.ColumnHeader>Name</Table.ColumnHeader>
            <Table.ColumnHeader>Description</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {groups.map((group) => (
            <Table.Row key={group.id}>
              <Table.Cell>{group.id}</Table.Cell>
              <Table.Cell>{group.name}</Table.Cell>
              <Table.Cell>{group.description}</Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
    </Box>
  );
}
