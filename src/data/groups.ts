export interface Group {
  id: string;
  name: string;
  description: string;
}

export const groups: Group[] = [
  {
    id: '201',
    name: 'Admins',
    description: 'Users with administrative privileges.',
  },
  {
    id: '202',
    name: 'Developers',
    description: 'Users involved in software development.',
  },
  {
    id: '203',
    name: 'Guests',
    description: 'Temporary users with limited access.',
  },
];