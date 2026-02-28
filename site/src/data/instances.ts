export interface Instance {
  step: number;
  name: string;
  description: string;
  phone?: string;
  email?: string;
  address?: string;
  url?: string;
  deadline: string;
  basis?: string;
}

export const instances: Instance[] = [
  {
    step: 1,
    name: 'Управляющая компания',
    description: 'Любая проблема — начинать с письменного обращения в УК. Обязательно с отметкой о вручении или заказным письмом.',
    phone: '+7 (812) 677-98-02',
    email: 'info@ecvida-service.ru',
    address: 'СПб, ул. Есенина, д. 9, к. 1, лит. А',
    deadline: '10 рабочих дней',
    basis: 'ЗоЗПП',
  },
  {
    step: 2,
    name: 'Государственная жилищная инспекция (ГЖИ)',
    description: 'УК не реагирует, нарушения содержания дома, нарушения лицензионных требований.',
    address: 'TODO: уточнить',
    email: 'TODO',
    deadline: '30 дней',
    basis: 'ст. 20 ЖК РФ, КоАП 7.22',
  },
  {
    step: 3,
    name: 'Роспотребнадзор',
    description: 'Качество воды, санитарные нарушения, нарушение прав потребителей ЖКУ.',
    address: 'TODO',
    email: 'TODO',
    deadline: '30 дней',
    basis: 'СанПиН 1.2.3685-21',
  },
  {
    step: 4,
    name: 'Прокуратура Петроградского района',
    description: 'Систематические нарушения, бездействие УК и надзорных органов, хищение средств.',
    address: 'TODO',
    email: 'TODO',
    deadline: '30 дней',
    basis: 'ФЗ «О прокуратуре», ст. 161 ЖК РФ',
  },
  {
    step: 5,
    name: 'МО Аптекарский остров',
    description: 'Благоустройство территории, нарушения на прилегающей территории.',
    address: 'TODO',
    email: 'TODO',
    deadline: '30 дней',
  },
  {
    step: 6,
    name: 'ГИС ЖКХ',
    description: 'Дублировать любые обращения через ГИС ЖКХ для электронной фиксации. Сроки контролируются системой.',
    url: 'https://dom.gosuslugi.ru',
    deadline: '10-30 дней',
    basis: 'Авторизация через Госуслуги',
  },
  {
    step: 7,
    name: 'Комитет по тарифам СПб',
    description: 'Завышенные тарифы на ЖКУ, необоснованные начисления.',
    address: 'TODO',
    email: 'TODO',
    deadline: '30 дней',
  },
  {
    step: 8,
    name: 'Петроградский районный суд',
    description: 'Крайняя мера — возмещение ущерба, понуждение к исполнению обязательств.',
    url: 'https://sudrf.ru',
    address: 'TODO',
    deadline: 'По регламенту суда',
    basis: 'ГК РФ ст. 15, 1064; ЖК РФ ст. 161-162',
  },
];

export const escalationSteps = [
  'УК (ЭКВИДА-СЕРВИС) — письменное обращение',
  'ГЖИ + ГИС ЖКХ — параллельно (если нет ответа 10 дней / отказ)',
  'Прокуратура + Роспотребнадзор (если нет результата 30 дней)',
  'Суд — исковое заявление (крайняя мера)',
];
