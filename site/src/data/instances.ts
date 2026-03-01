export interface Instance {
  id: string;
  step: number;
  name: string;
  description: string;
  phone?: string;
  email?: string;
  address?: string;
  url?: string;
  onlineForm?: string;
  deadline: string;
  basis?: string;
  workingHours?: string;
}

export const instances: Instance[] = [
  {
    id: 'uk',
    step: 1,
    name: 'Управляющая компания',
    description: 'Любая проблема — начинать с письменного обращения в УК. Обязательно с отметкой о вручении или заказным письмом.',
    phone: '+7 (812) 677-98-02',
    email: 'info@ecvida-service.ru',
    address: 'СПб, ул. Есенина, д. 9, к. 1, лит. А',
    deadline: '10 рабочих дней',
    basis: 'ЗоЗПП',
    workingHours: 'Чт, 09:00-16:00',
  },
  {
    id: 'gzhi',
    step: 2,
    name: 'Государственная жилищная инспекция (ГЖИ)',
    description: 'УК не реагирует, нарушения содержания дома, нарушения лицензионных требований.',
    phone: '+7 (812) 576-07-01',
    email: 'gzhi@gov.spb.ru',
    address: 'СПб, Малоохтинский пр., д. 68, лит. А',
    url: 'https://www.gov.spb.ru/gov/otrasl/inspekcija/',
    onlineForm: 'https://letters.gov.spb.ru/reception/',
    deadline: '30 дней',
    basis: 'ст. 20 ЖК РФ, КоАП 7.22',
    workingHours: 'Пн-чт: 9:00-18:00, Пт: 9:00-17:00',
  },
  {
    id: 'rospotrebnadzor',
    step: 3,
    name: 'Роспотребнадзор',
    description: 'Качество воды, санитарные нарушения, нарушение прав потребителей ЖКУ.',
    phone: '+7 (812) 232-15-92',
    email: 'to_sever@78rospotrebnadzor.ru',
    address: 'СПб, ул. Большая Пушкарская, д. 18 (Северный отдел)',
    url: 'https://78.rospotrebnadzor.ru',
    onlineForm: 'https://petition.rospotrebnadzor.ru/petition/',
    deadline: '30 дней',
    basis: 'СанПиН 1.2.3685-21',
  },
  {
    id: 'prokuratura',
    step: 4,
    name: 'Прокуратура Петроградского района',
    description: 'Систематические нарушения, бездействие УК и надзорных органов, хищение средств.',
    phone: '+7 (812) 232-05-09',
    email: 'kanz_ptr@procspb.ru',
    address: 'СПб, ул. Большая Монетная, д. 27а',
    onlineForm: 'https://epp.genproc.gov.ru/ru/proc_78/',
    deadline: '30 дней',
    basis: 'ФЗ «О прокуратуре», ст. 161 ЖК РФ',
  },
  {
    id: 'mo',
    step: 5,
    name: 'МО Аптекарский остров',
    description: 'Благоустройство территории, нарушения на прилегающей территории.',
    phone: '+7 (812) 702-12-02',
    email: 'mamo61@yandex.ru',
    address: 'СПб, ул. Льва Толстого, д. 5',
    url: 'http://msapt-ostrov.ru',
    deadline: '30 дней',
    workingHours: 'Приём Главы МО: Чт, 15:00-18:00',
  },
  {
    id: 'gis',
    step: 6,
    name: 'ГИС ЖКХ',
    description: 'Дублировать любые обращения через ГИС ЖКХ для электронной фиксации. Сроки контролируются системой.',
    url: 'https://dom.gosuslugi.ru',
    deadline: '10-30 дней',
    basis: 'Авторизация через Госуслуги',
  },
  {
    id: 'tariffs',
    step: 7,
    name: 'Комитет по тарифам СПб',
    description: 'Завышенные тарифы на ЖКУ, необоснованные начисления.',
    phone: '+7 (812) 576-21-50',
    email: 'rek@gov.spb.ru',
    address: 'СПб, ул. Садовая, д. 14/52, лит. А',
    url: 'https://tarifspb.ru',
    deadline: '30 дней',
  },
  {
    id: 'court',
    step: 8,
    name: 'Петроградский районный суд',
    description: 'Крайняя мера — возмещение ущерба, понуждение к исполнению обязательств.',
    phone: '+7 (812) 235-45-45',
    email: 'pgr.spb@sudrf.ru',
    address: 'СПб, ул. Съезжинская, д. 9/6',
    url: 'https://pgr.spb.sudrf.ru',
    deadline: 'По регламенту суда',
    basis: 'ГК РФ ст. 15, 1064; ЖК РФ ст. 161-162',
    workingHours: 'Пн-чт: 9:00-18:00, Пт: 9:00-17:00',
  },
];

export interface EscalationLevel {
  level: number;
  title: string;
  description: string;
  when: string;
}

export const escalationLevels: EscalationLevel[] = [
  {
    level: 1,
    title: 'Управляющая компания',
    description: 'Письменное обращение в УК ЭКВИДА-СЕРВИС с отметкой о вручении',
    when: 'Первый шаг при любой проблеме',
  },
  {
    level: 2,
    title: 'Надзорные органы',
    description: 'ГЖИ + ГИС ЖКХ параллельно, Роспотребнадзор по санитарным вопросам',
    when: 'УК не ответила 10 дней или отказала',
  },
  {
    level: 3,
    title: 'Прокуратура',
    description: 'Прокуратура Петроградского района — проверка законности действий УК',
    when: 'Надзорные органы не помогли за 30 дней',
  },
  {
    level: 4,
    title: 'Суд',
    description: 'Исковое заявление в Петроградский районный суд',
    when: 'Крайняя мера — возмещение ущерба, понуждение к исполнению',
  },
];
