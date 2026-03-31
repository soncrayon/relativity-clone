import { StrictMode, Suspense } from 'react';
import { createRoot } from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router';
import { Provider } from '@/components/ui/provider';
import { Center, Spinner } from '@chakra-ui/react';
import './index.css';

const router = createBrowserRouter([
  {
    path: '/',
    lazy: async () => {
      const { default: Component } = await import('./Layout');
      return { Component };
    },
    children: [
      {
        index: true,
        lazy: async () => {
          const { default: Component } = await import('./components/Home');
          return { Component };
        },
      },
      {
        path: 'workspaces',
        lazy: async () => {
          const [{ default: Component }, { loader }] = await Promise.all([
            import('./components/Workspaces'),
            import('./loaders/workspaces'),
          ]);
          return { Component, loader };
        },
      },
      {
        path: 'users',
        lazy: async () => {
          const [{ default: Component }, { loader }] = await Promise.all([
            import('./components/Users'),
            import('./loaders/users'),
          ]);
          return { Component, loader };
        },
      },
      {
        path: 'groups',
        lazy: async () => {
          const [{ default: Component }, { loader }] = await Promise.all([
            import('./components/Groups'),
            import('./loaders/groups'),
          ]);
          return { Component, loader };
        },
      },
    ],
  },
]);

createRoot(document.getElementById('root')!).render(
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
