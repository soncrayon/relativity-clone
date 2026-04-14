import { useRouteError, isRouteErrorResponse, Link } from "react-router";
import { Box, Heading, Text, Button } from "@chakra-ui/react";

const RouteError = () => {
  const error = useRouteError();

  let title = "Something went wrong";
  let message = "An unexpected error occurred.";

  if (isRouteErrorResponse(error)) {
    title = `${error.status} ${error.statusText}`;
    message = error.data?.message ?? error.statusText;
  } else if (error instanceof Error) {
    if (error.message.includes("Failed to fetch")) {
      title = "Cannot reach the server";
      message =
        "The API server isn't responding. Make sure the backend is running on http://localhost:8000.";
    } else {
      message = error.message;
    }
  }

  return (
    <Box p="8" maxW="600px">
      <Heading size="xl" mb="3" color="red.600">
        {title}
      </Heading>
      <Text mb="6" color="gray.600">
        {message}
      </Text>
      <Button asChild variant="outline" size="sm">
        <Link to="/">Go home</Link>
      </Button>
    </Box>
  );
};

export default RouteError;
