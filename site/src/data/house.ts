export const house = {
  name: 'Skandi Klubb',
  address: 'Санкт-Петербург, Аптекарский проспект, 18, литера А',
  district: 'Петроградский',
  developer: 'Bonava (NCC)',
  yearBuilt: 2016,
  cadastralNumber: '78:07:0003299:1239',
  totalArea: '138 680 м²',
  totalAreaNote: 'требует проверки',
  apartments: 1222,
  apartmentsNote: 'требует проверки',
  entrances: 31,
  elevators: 31,
  floors: '2-11 этажей (разные секции)',
  queues: [
    { number: 1, entrances: '1-8' },
    { number: 2, entrances: '9-16' },
    { number: 3, entrances: '17-25' },
    { number: 4, entrances: '26-31' },
  ],
  facilities: [
    { type: 'Нежилые помещения', description: 'Магазины на 1 этаже' },
    { type: 'Подземный паркинг', description: 'Есть, с рядом проблем' },
    { type: 'Кладовки', description: 'Под домом, частная собственность' },
  ],
} as const;

export const managementCompany = {
  name: 'ООО «ЭКВИДА-СЕРВИС»',
  inn: '7802355579',
  ogrn: '5067847029465',
  legalAddress: '197022, СПб, Аптекарский пр-кт, д. 18, лит. А, пом. 501-Н',
  officeAddress: 'СПб, ул. Есенина, д. 9, корп. 1, лит. А',
  phone: '+7 (812) 677-98-02',
  email: 'info@ecvida-service.ru',
  director: 'Иванов Алексей Викторович',
  directorSince: 'декабрь 2022',
  managingSince: '13.09.2016',
  schedule: {
    weekdays: 'Пн-Чт: 09:00-18:00 (перерыв 13:00-14:00)',
    friday: 'Пт: 09:00-17:00 (перерыв 13:00-14:00)',
    reception: 'Приём граждан: только Чт, 09:00-16:00',
  },
} as const;
