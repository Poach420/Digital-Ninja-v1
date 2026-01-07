import { Template } from '@/types';

export const templates: Template[] = [
  {
    id: 'react-starter',
    name: 'React Starter',
    description: 'A basic React application with TypeScript',
    framework: 'react',
    tags: ['react', 'typescript', 'starter'],
    files: [],
  },
  {
    id: 'next-blog',
    name: 'Next.js Blog',
    description: 'A modern blog built with Next.js and MDX',
    framework: 'next',
    tags: ['nextjs', 'blog', 'mdx'],
    files: [],
  },
  {
    id: 'dashboard-app',
    name: 'Dashboard Template',
    description: 'A complete dashboard with charts and analytics',
    framework: 'react',
    tags: ['dashboard', 'analytics', 'charts'],
    files: [],
  },
  {
    id: 'ecommerce',
    name: 'E-commerce Store',
    description: 'Full-featured e-commerce application',
    framework: 'next',
    tags: ['ecommerce', 'shop', 'stripe'],
    files: [],
  },
  {
    id: 'landing-page',
    name: 'Landing Page',
    description: 'Responsive landing page template',
    framework: 'react',
    tags: ['landing', 'marketing', 'responsive'],
    files: [],
  },
];

export const getTemplateById = (id: string): Template | undefined => {
  return templates.find(t => t.id === id);
};

export const getTemplatesByFramework = (framework: string): Template[] => {
  return templates.filter(t => t.framework === framework);
};
