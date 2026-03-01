export interface QuorumRow {
  category: string;
  items: {
    question: string;
    votes: string;
    example?: string;
    law: string;
  }[];
}

export interface RegistryStep {
  step: number;
  title: string;
  description: string;
  tip?: string;
}

export interface LawCard {
  id: string;
  title: string;
  article: string;
  category: 'housing' | 'consumer' | 'administrative' | 'civil';
  description: string;
  relevantProblems?: string[];
}

export interface ProblemLawLink {
  problem: string;
  problemSlug: string;
  laws: string[];
  instance: string;
  instanceHref: string;
}

const categoryLabels: Record<LawCard['category'], string> = {
  housing: 'Жилищное право',
  consumer: 'Защита потребителей',
  administrative: 'Административное право',
  civil: 'Гражданское право',
};

const categoryColors: Record<LawCard['category'], string> = {
  housing: 'bg-primary-50 text-primary-700 border-primary-200',
  consumer: 'bg-green-50 text-green-700 border-green-200',
  administrative: 'bg-red-50 text-red-700 border-red-200',
  civil: 'bg-purple-50 text-purple-700 border-purple-200',
};

export { categoryLabels, categoryColors };

export const quorumInfo = {
  principle: '1 кв.м = 1 голос (ч. 3 ст. 48 ЖК РФ)',
  quorumThreshold: 'Собрание правомочно при участии собственников с >50% голосов от общей площади (ч. 3 ст. 45 ЖК РФ)',
  commonMistake: 'Считать по числу собственников, а не по площади. 10% — это не 10% жителей, а собственники, владеющие 10% площади дома.',
};

export const quorumTable: QuorumRow[] = [
  {
    category: 'Совет МКД',
    items: [
      { question: 'Выбор/переизбрание совета, председателя', votes: '>50% участников', law: 'ст. 161.1 ЖК РФ' },
      { question: 'Наделение совета полномочиями по текущему ремонту', votes: '>50% от всех', law: 'ч. 4.2 ст. 44 ЖК РФ' },
      { question: 'Расширенные полномочия председателя (договоры, суд)', votes: '2/3 от всех', example: 'Право заключать договоры от имени собственников', law: 'п. 4.3, 5 ч. 2 ст. 44 ЖК РФ' },
    ],
  },
  {
    category: 'Управление и УК',
    items: [
      { question: 'Выбор способа управления МКД', votes: '>50% от всех', law: 'ст. 161 ЖК РФ' },
      { question: 'Выбор управляющей организации', votes: '>50% от всех', law: 'ст. 162 ЖК РФ' },
      { question: 'Отказ от договора управления', votes: '>50% участников', law: 'ст. 162 ЖК РФ' },
      { question: 'Создание ТСЖ', votes: '>50% от всех', law: 'ст. 135 ЖК РФ' },
    ],
  },
  {
    category: 'Общее имущество',
    items: [
      { question: 'Пользование ОДИ третьими лицами (провайдеры, реклама)', votes: '2/3 от всех', example: 'Сдача подвала в аренду, размещение рекламы', law: 'п. 3 ч. 2 ст. 44 ЖК РФ' },
      { question: 'Присоединение части ОДИ (уменьшение)', votes: '100% всех', example: 'Присоединение тамбура к квартире', law: 'ч. 3 ст. 36 ЖК РФ' },
      { question: 'Реконструкция МКД', votes: '2/3 от всех', law: 'п. 1 ч. 2 ст. 44 ЖК РФ' },
    ],
  },
  {
    category: 'Капитальный ремонт',
    items: [
      { question: 'Выбор способа формирования фонда', votes: '>50% от всех', law: 'ч. 3 ст. 170 ЖК РФ' },
      { question: 'Размер взноса выше минимального', votes: '2/3 от всех', law: 'ч. 1 ст. 169 ЖК РФ' },
      { question: 'Получение кредита на капремонт', votes: '2/3 от всех', law: 'п. 1.2 ч. 2 ст. 44 ЖК РФ' },
    ],
  },
  {
    category: 'Текущий ремонт',
    items: [
      { question: 'Текущий ремонт общего имущества', votes: '>50% участников', law: 'п. 4.1 ч. 2 ст. 44 ЖК РФ' },
      { question: 'Благоустройство земельного участка', votes: '>50% участников', law: 'п. 2.1 ч. 2 ст. 44 ЖК РФ' },
    ],
  },
  {
    category: 'Проведение собраний',
    items: [
      { question: 'Способ уведомления о собрании', votes: '>50% участников', law: 'ч. 4 ст. 45 ЖК РФ' },
      { question: 'Использование ГИС ЖКХ для голосования', votes: '>50% участников', law: 'ч. 1 ст. 47.1 ЖК РФ' },
      { question: 'Переход на прямые договоры с РСО', votes: '>50% участников', law: 'ч. 4.4 ст. 44 ЖК РФ' },
    ],
  },
];

export const importantThresholds = [
  { threshold: '10% площади', purpose: 'Инициировать созыв ОСС', law: 'ч. 6 ст. 45 ЖК РФ' },
  { threshold: '50%+1 голос', purpose: 'Кворум — собрание считается состоявшимся', law: 'ч. 3 ст. 45 ЖК РФ' },
  { threshold: '>50%', purpose: 'Простое большинство решений', law: 'ч. 1 ст. 46 ЖК РФ' },
  { threshold: '2/3 голосов', purpose: 'Капремонт, распоряжение ОИ, реконструкция', law: 'п. 1-3 ч. 2 ст. 44 ЖК РФ' },
  { threshold: '100%', purpose: 'Уменьшение общего имущества', law: 'ч. 3 ст. 36 ЖК РФ' },
];

export const registrySteps: RegistryStep[] = [
  {
    step: 1,
    title: 'Подготовьте заявление',
    description: 'Письменное заявление на имя директора УК с просьбой предоставить реестр собственников помещений МКД для проведения ОСС.',
    tip: 'Укажите цель — проведение ОСС. УК не вправе отказать или требовать подтверждения.',
  },
  {
    step: 2,
    title: 'Подайте в УК с отметкой',
    description: 'Подайте заявление лично с отметкой на вашем экземпляре (дата, подпись, входящий номер) или заказным письмом с уведомлением.',
    tip: 'Можно также через ГИС ЖКХ или электронную почту с подтверждением.',
  },
  {
    step: 3,
    title: 'Ожидайте 5 рабочих дней',
    description: 'УК обязана предоставить реестр в течение 5 рабочих дней с момента получения заявления (ч. 3.1 ст. 45 ЖК РФ).',
    tip: 'Согласие других собственников на передачу их данных НЕ требуется.',
  },
  {
    step: 4,
    title: 'При отказе — жалуйтесь',
    description: 'Если УК отказала или не ответила — жалоба в ГЖИ СПб. Штраф за отказ: 250 000 — 300 000 рублей (ч. 1 ст. 7.23.3 КоАП РФ).',
    tip: 'ГЖИ СПб: наб. канала Грибоедова, 88-90, тел. +7 (812) 576-07-01',
  },
];

export const registryInfo = {
  legalBasis: 'ч. 3.1 ст. 45 ЖК РФ',
  whoKeeps: 'Управляющая организация (УК)',
  whoCanRequest: 'Любой собственник помещения в МКД',
  deadline: '5 рабочих дней',
  penaltyForRefusal: '250 000 — 300 000 руб.',
  penaltyBasis: 'ч. 1 ст. 7.23.3 КоАП РФ',
  personalDataNote: 'Согласие других собственников НЕ требуется (п. 2 ч. 1 ст. 6 ФЗ «О персональных данных»)',
  change2025: 'С 1 сентября 2025 — реестр больше не обязательное приложение к протоколу ОСС, но обязанность вести и предоставлять сохраняется.',
};

export const laws: LawCard[] = [
  {
    id: 'zhk-161',
    title: 'Выбор способа управления МКД',
    article: 'ст. 161 ЖК РФ',
    category: 'housing',
    description: 'Собственники обязаны выбрать способ управления МКД. УК несёт ответственность за содержание общего имущества.',
    relevantProblems: ['management'],
  },
  {
    id: 'zhk-162',
    title: 'Договор управления МКД',
    article: 'ст. 162 ЖК РФ',
    category: 'housing',
    description: 'Условия и порядок заключения, изменения и расторжения договора управления. Права собственников на отказ от договора.',
    relevantProblems: ['management'],
  },
  {
    id: 'zhk-161-1',
    title: 'Совет МКД и председатель',
    article: 'ст. 161.1 ЖК РФ',
    category: 'housing',
    description: 'Если в МКД не создано ТСЖ — собственники обязаны избрать совет дома. Совет контролирует УК, выступает от имени собственников.',
  },
  {
    id: 'zhk-44-46',
    title: 'Общее собрание собственников',
    article: 'ст. 44-48 ЖК РФ',
    category: 'housing',
    description: 'Компетенция, порядок проведения, кворум, порядок принятия решений на ОСС.',
  },
  {
    id: 'zhk-36',
    title: 'Право собственности на общее имущество',
    article: 'ст. 36 ЖК РФ',
    category: 'housing',
    description: 'Собственникам помещений принадлежит на праве общей долевой собственности общее имущество в МКД.',
    relevantProblems: ['parking', 'territory'],
  },
  {
    id: 'pp-491',
    title: 'Правила содержания общего имущества',
    article: 'ПП РФ №491 от 13.08.2006',
    category: 'housing',
    description: 'Определяет состав общего имущества, требования к содержанию и порядок контроля. Основа для проверок ГЖИ.',
    relevantProblems: ['facade', 'roof', 'elevator', 'engineering'],
  },
  {
    id: 'koap-7-22',
    title: 'Нарушение правил содержания жилых домов',
    article: 'ст. 7.22 КоАП РФ',
    category: 'administrative',
    description: 'Штраф для юрлиц 40 000 — 50 000 руб. за нарушение правил содержания и ремонта жилых домов.',
    relevantProblems: ['facade', 'roof', 'elevator', 'engineering', 'fire-safety'],
  },
  {
    id: 'koap-7-23-3',
    title: 'Отказ в предоставлении реестра',
    article: 'ст. 7.23.3 КоАП РФ',
    category: 'administrative',
    description: 'Штраф 250 000 — 300 000 руб. за отказ в предоставлении реестра собственников.',
  },
  {
    id: 'zozpp',
    title: 'Закон о защите прав потребителей',
    article: 'ФЗ №2300-1',
    category: 'consumer',
    description: 'Собственник — потребитель услуг УК. Право на качество, информацию, возмещение вреда, неустойку.',
    relevantProblems: ['management', 'engineering'],
  },
  {
    id: 'gk-15',
    title: 'Возмещение убытков',
    article: 'ст. 15, 1064 ГК РФ',
    category: 'civil',
    description: 'Право на полное возмещение убытков, причинённых ненадлежащим исполнением обязательств.',
    relevantProblems: ['roof', 'engineering'],
  },
  {
    id: 'sanpin',
    title: 'Санитарные нормы',
    article: 'СанПиН 1.2.3685-21',
    category: 'consumer',
    description: 'Гигиенические нормативы по качеству воды, воздуха, уровню шума, освещённости.',
    relevantProblems: ['engineering', 'territory'],
  },
  {
    id: 'pp-1479',
    title: 'Правила противопожарного режима',
    article: 'ПП РФ №1479',
    category: 'administrative',
    description: 'Требования к содержанию путей эвакуации, систем АППЗ, шлагбаумам (диспетчеризация для 112).',
    relevantProblems: ['fire-safety'],
  },
];

export const problemLawLinks: ProblemLawLink[] = [
  {
    problem: 'Фасад и кровля',
    problemSlug: 'facade',
    laws: ['ПП РФ №491', 'ст. 7.22 КоАП'],
    instance: 'ГЖИ',
    instanceHref: '/complaints',
  },
  {
    problem: 'Лифты',
    problemSlug: 'elevator',
    laws: ['ПП РФ №491', 'ТР ТС 011/2011'],
    instance: 'Ростехнадзор, ГЖИ',
    instanceHref: '/complaints',
  },
  {
    problem: 'Инженерные сети',
    problemSlug: 'engineering',
    laws: ['ПП РФ №491', 'ст. 7.22 КоАП'],
    instance: 'ГЖИ',
    instanceHref: '/complaints',
  },
  {
    problem: 'Пожарная безопасность',
    problemSlug: 'fire-safety',
    laws: ['ПП РФ №1479', 'ст. 20.4 КоАП'],
    instance: 'МЧС, прокуратура',
    instanceHref: '/complaints',
  },
  {
    problem: 'Паркинг',
    problemSlug: 'parking',
    laws: ['ст. 36 ЖК РФ', 'ПП РФ №491'],
    instance: 'ГЖИ',
    instanceHref: '/complaints',
  },
  {
    problem: 'Территория',
    problemSlug: 'territory',
    laws: ['ПП РФ №491', 'СанПиН'],
    instance: 'ГЖИ, Роспотребнадзор',
    instanceHref: '/complaints',
  },
  {
    problem: 'Управление',
    problemSlug: 'management',
    laws: ['ст. 161-162 ЖК РФ', 'ЗоЗПП'],
    instance: 'ГЖИ, прокуратура',
    instanceHref: '/complaints',
  },
];
