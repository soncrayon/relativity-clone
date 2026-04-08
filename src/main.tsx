import { StrictMode, Suspense } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router";
import { Provider } from "@/components/ui/provider";
import { Center, Spinner } from "@chakra-ui/react";
import { router } from "@/router";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Provider>
      <Suspense
        fallback={
          <Center height="100vh">
            <Spinner size="xl" borderWidth="4px" />
          </Center>
        }
      >
        <RouterProvider router={router} />
      </Suspense>
    </Provider>
  </StrictMode>,
);
