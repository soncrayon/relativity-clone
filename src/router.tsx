import { createBrowserRouter } from "react-router";
import RouteError from "@/components/RouteError";

export const router = createBrowserRouter([
  {
    path: "/",
    errorElement: <RouteError />,
    lazy: async () => {
      const { default: Component } = await import("@/Layout");
      return { Component };
    },
    children: [
      {
        index: true,
        lazy: async () => {
          const { default: Component } = await import("@/components/Home");
          return { Component };
        },
      },
      {
        path: "workspaces",
        lazy: async () => {
          const [{ default: Component }, { loader }] = await Promise.all([
            import("@/features/workspaces/components/Workspaces"),
            import("@/features/workspaces/loaders"),
          ]);
          return { Component, loader };
        },
      },
      {
        path: "users",
        lazy: async () => {
          const [{ default: Component }, { loader }] = await Promise.all([
            import("@/features/users/components/Users"),
            import("@/features/users/loaders"),
          ]);
          return { Component, loader };
        },
      },
      {
        path: "groups",
        lazy: async () => {
          const [{ default: Component }, { loader }] = await Promise.all([
            import("@/features/groups/components/Groups"),
            import("@/features/groups/loaders"),
          ]);
          return { Component, loader };
        },
      },
    ],
  },
]);
