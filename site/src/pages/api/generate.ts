export const prerender = false;

import type { APIRoute } from 'astro';
import { complaintTemplates, instanceHeaders } from '../../data/complaint-templates';
import { instances } from '../../data/instances';

// In-memory rate limiting (resets on server restart)
const rateLimitMap = new Map<string, { count: number; resetAt: number }>();

function checkRateLimit(ip: string): boolean {
  const now = Date.now();
  const entry = rateLimitMap.get(ip);

  if (!entry || now > entry.resetAt) {
    rateLimitMap.set(ip, { count: 1, resetAt: now + 3600_000 });
    return true;
  }

  if (entry.count >= 10) {
    return false;
  }

  entry.count++;
  return true;
}

// Clean up old entries periodically
setInterval(() => {
  const now = Date.now();
  for (const [ip, entry] of rateLimitMap) {
    if (now > entry.resetAt) rateLimitMap.delete(ip);
  }
}, 600_000);

interface GenerateRequest {
  problemSlug: string;
  instanceId: string;
  residentData?: {
    fullName?: string;
    apartment?: string;
    area?: string;
    entrance?: string;
    phone?: string;
    email?: string;
    previousDate?: string;
  };
  customDescription?: string;
}

function buildPrompt(template: typeof complaintTemplates[0], req: GenerateRequest): string {
  const instHeader = instanceHeaders[template.instanceId] || '';
  const instance = instances.find(i => i.id === template.instanceId);
  const rd = req.residentData || {};

  const residentBlock = rd.fullName
    ? `Данные заявителя: ${rd.fullName}, кв. ${rd.apartment || '___'}${rd.area ? `, площадь ${rd.area}` : ''}${rd.phone ? `, тел. ${rd.phone}` : ''}${rd.email ? `, email ${rd.email}` : ''}`
    : 'Данные заявителя не указаны — используй плейсхолдеры [ФИО собственника], [кв. ___], [телефон], [email]';

  const prevDate = rd.previousDate
    ? new Date(rd.previousDate).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
    : null;

  return `Ты — юрист-консультант по жилищному праву РФ. Составь официальное обращение (жалобу).

СТРОГИЕ ПРАВИЛА:
- Используй ТОЛЬКО указанные нормативные акты — НЕ выдумывай другие
- Деловой стиль, формат официального заявления
- Адрес дома: Санкт-Петербург, Аптекарский пр-кт, д. 18, лит. А
- УК: ООО «ЭКВИДА-СЕРВИС» (ИНН 7802355579)
- НЕ выдумывай факты, которых нет в контексте
- Если данные заявителя не указаны — оставляй плейсхолдеры в квадратных скобках
- Верни ТОЛЬКО текст обращения, без комментариев и пояснений

ШАПКА ОБРАЩЕНИЯ:
${instHeader}

${residentBlock}

ИНСТАНЦИЯ: ${instance?.name || template.instanceId}

ПРОБЛЕМА: ${template.problemTitle}

ТЕЛО ШАБЛОНА (используй как основу, улучши и персонализируй):
${template.bodyTemplate.replace(/\{\{fullName\}\}/g, rd.fullName || '[ФИО собственника]')
  .replace(/\{\{apartment\}\}/g, rd.apartment || '[кв. ___]')
  .replace(/\{\{area\}\}/g, rd.area || '[площадь]')
  .replace(/\{\{phone\}\}/g, rd.phone || '[телефон]')
  .replace(/\{\{email\}\}/g, rd.email || '[email]')
  .replace(/\{\{entrance\}\}/g, rd.entrance || '[парадная]')
  .replace(/\{\{previousDate\}\}/g, prevDate || '__.__.____')}

НОРМАТИВНАЯ БАЗА (использовать строго):
${template.legalBasis.join('\n')}

ТРЕБОВАНИЯ (ПРОШУ):
${template.demands.map((d, i) => `${i + 1}. ${d}`).join('\n')}

${template.attachments.length > 0 ? `ПРИЛОЖЕНИЯ:\n${template.attachments.map((a, i) => `${i + 1}. ${a}`).join('\n')}` : ''}

${req.customDescription ? `ОПИСАНИЕ СИТУАЦИИ ОТ ЖИТЕЛЯ (персонализируй обращение на основе этого):\n${req.customDescription.slice(0, 1000)}` : ''}

Формат ответа: только текст обращения, готовый к печати.`;
}

export const POST: APIRoute = async ({ request }) => {
  const ip = request.headers.get('x-forwarded-for')?.split(',')[0]?.trim()
    || request.headers.get('x-real-ip')
    || 'unknown';

  if (!checkRateLimit(ip)) {
    return new Response(
      JSON.stringify({ error: 'Превышен лимит запросов. Попробуйте через час.' }),
      { status: 429, headers: { 'Content-Type': 'application/json' } }
    );
  }

  let body: GenerateRequest;
  try {
    body = await request.json();
  } catch {
    return new Response(
      JSON.stringify({ error: 'Некорректный JSON' }),
      { status: 400, headers: { 'Content-Type': 'application/json' } }
    );
  }

  const { problemSlug, instanceId, residentData: rd, customDescription } = body;

  if (!problemSlug || !instanceId) {
    return new Response(
      JSON.stringify({ error: 'problemSlug и instanceId обязательны' }),
      { status: 400, headers: { 'Content-Type': 'application/json' } }
    );
  }

  const template = complaintTemplates.find(
    t => t.problemSlug === problemSlug && t.instanceId === instanceId
  );

  if (!template) {
    return new Response(
      JSON.stringify({ error: 'Шаблон не найден' }),
      { status: 404, headers: { 'Content-Type': 'application/json' } }
    );
  }

  // Sanitize customDescription
  const safeDescription = customDescription?.slice(0, 1000) || '';

  const apiKey = import.meta.env.OPENROUTER_API_KEY;

  if (!apiKey) {
    // No API key — return template-based generation signal
    return new Response(
      JSON.stringify({ text: '', mode: 'template', warning: 'AI недоступен, используйте шаблон' }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  }

  const prompt = buildPrompt(template, {
    problemSlug,
    instanceId,
    residentData: rd,
    customDescription: safeDescription,
  });

  try {
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
        'HTTP-Referer': 'https://skklubb.ru',
        'X-Title': 'SkandiKlubb Complaint Generator',
      },
      body: JSON.stringify({
        model: 'anthropic/claude-haiku-4-20250414',
        messages: [
          { role: 'user', content: prompt },
        ],
        max_tokens: 2000,
        temperature: 0.3,
      }),
    });

    if (!response.ok) {
      const errText = await response.text();
      console.error('OpenRouter error:', response.status, errText);
      return new Response(
        JSON.stringify({ text: '', mode: 'template', warning: 'AI временно недоступен' }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const data = await response.json();
    const aiText = data.choices?.[0]?.message?.content?.trim();

    if (!aiText) {
      return new Response(
        JSON.stringify({ text: '', mode: 'template', warning: 'Пустой ответ от AI' }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      );
    }

    return new Response(
      JSON.stringify({ text: aiText, mode: 'ai' }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (err) {
    console.error('AI generation error:', err);
    return new Response(
      JSON.stringify({ text: '', mode: 'template', warning: 'Ошибка соединения с AI' }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  }
};
