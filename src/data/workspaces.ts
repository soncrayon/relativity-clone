export interface Workspace {
  id: string;
  name: string;
  description: string;
}

export const workspaces: Workspace[] = [
  {
    id: '1',
    name: 'Workspace Alpha',
    description: 'This is the first test workspace.',
  },
  {
    id: '2',
    name: 'Workspace Beta',
    description: 'This is the second test workspace.',
  },
  {
    id: '3',
    name: 'Workspace Gamma',
    description: 'This is the third test workspace.',
  },
];