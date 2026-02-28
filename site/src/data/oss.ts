export interface OssQuestion {
  number: number;
  notification: string;
  voting: string;
  quorum: string;
  status: 'preparing' | 'clarifying' | 'investigation' | 'waiting';
}

export interface OssBlock {
  title: string;
  legalBasis: string;
  questions: OssQuestion[];
  note?: string;
}

const statusLabels: Record<OssQuestion['status'], string> = {
  preparing: 'Подготовка',
  clarifying: 'Уточняется',
  investigation: 'Требуются изыскания',
  waiting: 'Ожидание сметы',
};

export { statusLabels };

export const ossBlocks: OssBlock[] = [
  {
    title: 'Совет многоквартирного дома',
    legalBasis: 'ч. 1, 4, 6 ст. 161.1, ч. 4.2, 4.3 ст. 44 ЖК РФ',
    questions: [
      { number: 1, notification: 'Выбор совета МКД', voting: 'Утвердить кандидатуры в совет МКД', quorum: '>50% участников', status: 'preparing' },
      { number: 2, notification: 'Утверждение количества членов совета МКД', voting: 'Утвердить состав членов совета МКД', quorum: '>50% участников', status: 'preparing' },
      { number: 3, notification: 'Выбор председателя совета МКД', voting: 'Утвердить председателем совета МКД', quorum: '>50% участников', status: 'preparing' },
      { number: 4, notification: 'Наделение совета МКД полномочиями на принятие решений о текущем ремонте', voting: 'Наделить совет МКД полномочиями на принятие решений о текущем ремонте общего имущества', quorum: '>50% от всех', status: 'preparing' },
      { number: 5, notification: 'Наделение председателя совета МКД полномочиями', voting: 'Принять решение о наделении председателя совета МКД расширенными полномочиями', quorum: '2/3 от всех', status: 'preparing' },
    ],
  },
  {
    title: 'Капитальный ремонт',
    legalBasis: 'ч. 3 ст. 170, ч. 1 ст. 173, ч. 2 ст. 175 ЖК РФ',
    questions: [
      { number: 6, notification: 'Формирование фонда капремонта на спецсчёте', voting: 'Формировать фонд капитального ремонта на специальном счёте', quorum: '>50% от всех', status: 'clarifying' },
      { number: 7, notification: 'Выбор владельца специального счёта', voting: 'Выбрать владельцем специального счёта УК', quorum: '>50% от всех', status: 'clarifying' },
      { number: 8, notification: 'Выбор банка для спецсчёта', voting: 'Выбрать кредитную организацию для открытия спецсчёта', quorum: '>50% от всех', status: 'clarifying' },
    ],
  },
  {
    title: 'Шлагбаум и СКУД',
    legalBasis: 'п. 2, 3 ч. 2 ст. 44 ЖК РФ',
    note: 'По ПП РФ №1479 шлагбаум обязан иметь диспетчеризацию для пропуска служб 112.',
    questions: [
      { number: 9, notification: 'Установка шлагбаума', voting: 'Принять решение об установке ограждающих устройств (шлагбаума)', quorum: '2/3 от всех', status: 'investigation' },
      { number: 10, notification: 'Модернизация СКУД', voting: 'Принять решение о модернизации системы контроля доступа', quorum: '2/3 от всех', status: 'investigation' },
      { number: 11, notification: 'Утверждение сметы на шлагбаум и СКУД', voting: 'Утвердить смету расходов на установку шлагбаума и модернизацию СКУД', quorum: '2/3 от всех', status: 'waiting' },
    ],
  },
  {
    title: 'Замена ворот',
    legalBasis: 'п. 1 ч. 2 ст. 44 ЖК РФ',
    questions: [
      { number: 12, notification: 'Замена распашных ворот', voting: 'Принять решение о замене распашных ворот на автоматические', quorum: '2/3 от всех', status: 'investigation' },
      { number: 13, notification: 'Утверждение сметы на замену ворот', voting: 'Утвердить смету расходов на замену ворот', quorum: '2/3 от всех', status: 'waiting' },
    ],
  },
];

export const quorumTable = [
  { type: 'Обычные вопросы', required: '>50% от участников собрания' },
  { type: 'Выбор способа управления, тариф', required: '>50% от всех собственников' },
  { type: 'Капремонт, распоряжение ОИ, шлагбаум', required: '2/3 от всех собственников' },
];

export const currentSituation = {
  council: 'Отсутствует',
  accessSystem: 'Брелоки + домофон',
  gates: 'Распашные, 2 въезда',
  barrier: 'Отсутствует',
};
