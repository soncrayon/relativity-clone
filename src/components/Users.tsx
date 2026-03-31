
import { useLoaderData } from 'react-router';
import { Box, Heading, Table } from '@chakra-ui/react';
import type { User } from '@/data/users';

export default function Users() {
  const { users } = useLoaderData() as { users: User[] };

  return (
    <Box>
      <Heading size="xl" mb="6">Users</Heading>
      <Table.Root size="md" variant="outline">
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader>ID</Table.ColumnHeader>
            <Table.ColumnHeader>Name</Table.ColumnHeader>
            <Table.ColumnHeader>Email</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {users.map((user) => (
            <Table.Row key={user.id}>
              <Table.Cell>{user.id}</Table.Cell>
              <Table.Cell>{user.name}</Table.Cell>
              <Table.Cell>{user.email}</Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
    </Box>
  );
}
