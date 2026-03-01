export interface ManagementDuty {
  obligation: string;
  clause: string;
  status: 'violated' | 'partial' | 'ok' | 'unknown';
  comment?: string;
}

export const managementDuties: ManagementDuty[] = [
  {
    obligation: 'Содержание и ремонт общего имущества',
    clause: 'п. 3.1.1',
    status: 'violated',
    comment: 'Фасад, кровля, подвалы — множественные нарушения',
  },
  {
    obligation: 'Готовность инженерных коммуникаций и приборов учёта',
    clause: 'п. 3.1.2',
    status: 'partial',
    comment: 'Проблемы с отоплением, ОДПУ',
  },
  {
    obligation: 'Пожарная безопасность в местах общего пользования',
    clause: 'п. 3.1.3',
    status: 'violated',
    comment: 'АППЗ не обслуживается, нет проверок',
  },
  {
    obligation: 'Подготовка к сезонной эксплуатации',
    clause: 'п. 3.1.4',
    status: 'partial',
  },
  {
    obligation: 'Текущий ремонт и содержание территории',
    clause: 'п. 3.1.6',
    status: 'violated',
    comment: 'Территория запущена, ремонт не проводится',
  },
  {
    obligation: 'Информирование о неполадках в течение суток',
    clause: 'п. 3.1.7',
    status: 'violated',
    comment: 'Уведомления отсутствуют или запоздалые',
  },
  {
    obligation: 'Рассмотрение обращений собственников',
    clause: 'п. 3.1.16',
    status: 'violated',
    comment: 'Обращения игнорируются или отписки',
  },
  {
    obligation: 'Ежегодный отчёт о выполнении договора (I квартал)',
    clause: 'п. 3.1.18',
    status: 'violated',
    comment: 'Отчёты не предоставляются',
  },
];

export const statusLabels: Record<ManagementDuty['status'], string> = {
  violated: 'Не выполняет',
  partial: 'Частично',
  ok: 'Выполняет',
  unknown: 'Неизвестно',
};

export const statusColors: Record<ManagementDuty['status'], { bg: string; text: string; dot: string }> = {
  violated: { bg: 'bg-red-50', text: 'text-red-700', dot: 'bg-red-500' },
  partial: { bg: 'bg-amber-50', text: 'text-amber-700', dot: 'bg-amber-500' },
  ok: { bg: 'bg-green-50', text: 'text-green-700', dot: 'bg-green-500' },
  unknown: { bg: 'bg-accent-50', text: 'text-accent-600', dot: 'bg-accent-400' },
};
