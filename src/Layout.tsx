import { Outlet, Link } from "react-router";
import { Box, Text, List } from "@chakra-ui/react";

const Layout = () => {
  return (
    <Box display="flex" height="100vh">
      <Box
        as="aside"
        width="250px"
        bg="#f0f0f0"
        p="4"
        borderRight="1px solid"
        borderColor="gray.200"
      >
        <Text as="h2" mt="0" mb="6" fontSize="1.5rem" color="gray.700">
          Relativity
        </Text>
        <List.Root listStyleType="none" p="0" m="0">
          <List.Item py="2" _hover={{ bg: "gray.200" }}>
            <Link
              to="/workspaces"
              style={{
                textDecoration: "none",
                color: "inherit",
                display: "block",
                padding: "0 0.5rem",
              }}
            >
              Workspaces
            </Link>
          </List.Item>
          <List.Item py="2" _hover={{ bg: "gray.200" }}>
            <Link
              to="/users"
              style={{
                textDecoration: "none",
                color: "inherit",
                display: "block",
                padding: "0 0.5rem",
              }}
            >
              Users
            </Link>
          </List.Item>
          <List.Item py="2" _hover={{ bg: "gray.200" }}>
            <Link
              to="/groups"
              style={{
                textDecoration: "none",
                color: "inherit",
                display: "block",
                padding: "0 0.5rem",
              }}
            >
              Groups
            </Link>
          </List.Item>
        </List.Root>
      </Box>
      <Box as="main" flexGrow="1" p="4" overflowY="auto">
        <Outlet />
      </Box>
    </Box>
  );
};

export default Layout;
