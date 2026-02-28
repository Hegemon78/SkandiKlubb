import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const problems = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/problems' }),
  schema: z.object({
    title: z.string(),
    category: z.enum(['Безопасность', 'Технические', 'Финансовые', 'Организационные']),
    priority: z.enum(['high', 'medium', 'low']),
    status: z.enum(['collecting', 'preparing', 'ready', 'investigation']),
    summary: z.string(),
    order: z.number(),
  }),
});

export const collections = { problems };
