export type Lang = 'ru' | 'kk';

export type TranslationKey =
  // Навигация
  | 'nav.live' | 'nav.alarms' | 'nav.zones' | 'nav.stats' | 'nav.settings' | 'nav.logs'
  // Камеры
  | 'camera.1' | 'camera.2' | 'camera.3'
  // Видео
  | 'video.connecting' | 'video.no_signal' | 'video.back_to_grid'
  // Тревоги
  | 'alarms.title' | 'alarms.sound_on' | 'alarms.sound_off'
  | 'alarms.empty' | 'alarms.resolved_section'
  // Карточка тревоги
  | 'plate.no_plate' | 'plate.confidence' | 'plate.in_zone'
  | 'plate.show_image' | 'plate.hide_image'
  | 'plate.resolve' | 'plate.delete'
  | 'plate.just_now' | 'plate.minutes_ago' | 'plate.hours_ago' | 'plate.days_ago'
  // Зоны
  | 'zone.title' | 'zone.name_placeholder' | 'zone.save' | 'zone.clear'
  | 'zone.drawing_hint' | 'zone.empty' | 'zone.active' | 'zone.inactive' | 'zone.delete'
  // Статистика
  | 'stats.total' | 'stats.active' | 'stats.resolved' | 'stats.cpu'
  | 'stats.camera_fps' | 'stats.system' | 'stats.ram' | 'stats.vram'
  | 'stats.camera_alarms' | 'stats.hourly_title' | 'stats.loading' | 'stats.no_data'
  // Настройки
  | 'settings.title' | 'settings.violation_duration' | 'settings.save'
  | 'settings.saved' | 'settings.minutes' | 'settings.seconds' | 'settings.camera_section'
  // Фильтр тревог
  | 'filter.plate' | 'filter.all_cameras' | 'filter.all_status'
  | 'filter.status_active' | 'filter.status_resolved'
  | 'filter.date_from' | 'filter.date_to' | 'filter.search' | 'filter.reset'
  | 'filter.total' | 'filter.prev' | 'filter.next' | 'filter.no_results' | 'filter.showing'
  // Логи
  | 'logs.title' | 'logs.clear' | 'logs.auto_scroll' | 'logs.filter_all'
  | 'logs.filter_info' | 'logs.filter_warn' | 'logs.filter_error'
  | 'logs.connecting' | 'logs.no_logs';

type Translations = Record<TranslationKey, string>;

export const translations: Record<Lang, Translations> = {
  ru: {
    // Навигация
    'nav.live':     'Прямой эфир',
    'nav.alarms':   'Тревоги',
    'nav.zones':    'Зоны',
    'nav.stats':    'Статистика',
    'nav.settings': 'Настройки',
    'nav.logs':     'Логи',

    // Камеры
    'camera.1': 'Въезд',
    'camera.2': 'Парковка-А',
    'camera.3': 'Парковка-Б',

    // Видео
    'video.connecting':  'Подключение...',
    'video.no_signal':   'Нет сигнала',
    'video.back_to_grid': 'К сетке',

    // Тревоги
    'alarms.title':            'Тревоги',
    'alarms.sound_on':         'Звук: ВКЛ',
    'alarms.sound_off':        'Звук: ВЫКЛ',
    'alarms.empty':            'Тревог пока нет',
    'alarms.resolved_section': 'Закрытые',

    // Карточка тревоги
    'plate.no_plate':    'НЕТ НОМЕРА',
    'plate.confidence':  'Точность:',
    'plate.in_zone':     'сек. в зоне',
    'plate.show_image':  'Фото',
    'plate.hide_image':  'Скрыть',
    'plate.resolve':     'Закрыть',
    'plate.delete':      'Удалить',
    'plate.just_now':    'Только что',
    'plate.minutes_ago': 'мин. назад',
    'plate.hours_ago':   'ч. назад',
    'plate.days_ago':    'дн. назад',

    // Зоны
    'zone.title':           'Зоны',
    'zone.name_placeholder': 'Название зоны...',
    'zone.save':             'Сохранить',
    'zone.clear':            'Очистить',
    'zone.drawing_hint':     'Лев. клик: добавить точку | Прав. клик: отменить | Мин. 3 точки',
    'zone.empty':            'Зон нет. Нажмите на canvas.',
    'zone.active':           'Активна',
    'zone.inactive':         'Неактивна',
    'zone.delete':           'Удалить',

    // Статистика
    'stats.total':         'Всего тревог',
    'stats.active':        'Активные',
    'stats.resolved':      'Закрытые',
    'stats.cpu':           'CPU',
    'stats.camera_fps':    'FPS камер',
    'stats.system':        'Система',
    'stats.ram':           'RAM',
    'stats.vram':          'VRAM',
    'stats.camera_alarms': 'Тревоги по камерам',
    'stats.hourly_title':  'Почасовое распределение тревог (Сегодня)',
    'stats.loading':       'Ожидание данных...',
    'stats.no_data':       'Данных пока нет',

    // Настройки
    'settings.title':              'Настройки камер',
    'settings.violation_duration': 'Время нарушения',
    'settings.save':               'Сохранить',
    'settings.saved':              '✓ Сохранено',
    'settings.minutes':            'мин.',
    'settings.seconds':            'сек.',
    'settings.camera_section':     'Камера',

    // Фильтр тревог
    'filter.plate':           'Поиск по номеру...',
    'filter.all_cameras':     'Все камеры',
    'filter.all_status':      'Все статусы',
    'filter.status_active':   'Активные',
    'filter.status_resolved': 'Закрытые',
    'filter.date_from':       'Дата от',
    'filter.date_to':         'Дата до',
    'filter.search':          'Найти',
    'filter.reset':           'Сброс',
    'filter.total':           'Всего',
    'filter.prev':            'Назад',
    'filter.next':            'Вперёд',
    'filter.no_results':      'Тревог не найдено',
    'filter.showing':         'Показано',

    // Логи
    'logs.title':        'Логи системы',
    'logs.clear':        'Очистить',
    'logs.auto_scroll':  'Авто-прокрутка',
    'logs.filter_all':   'Все',
    'logs.filter_info':  'INFO',
    'logs.filter_warn':  'WARN',
    'logs.filter_error': 'ERROR',
    'logs.connecting':   'Подключение...',
    'logs.no_logs':      'Логов нет',
  },

  kk: {
    // Навигация
    'nav.live':     'Тікелей трансляция',
    'nav.alarms':   'Дабылдар',
    'nav.zones':    'Аймақтар',
    'nav.stats':    'Статистика',
    'nav.settings': 'Параметрлер',
    'nav.logs':     'Журнал',

    // Камеры
    'camera.1': 'Кіріс есігі',
    'camera.2': 'Автотұрақ-А',
    'camera.3': 'Автотұрақ-Б',

    // Видео
    'video.connecting':  'Қосылуда...',
    'video.no_signal':   'Байланыс жоқ',
    'video.back_to_grid': 'Торға оралу',

    // Тревоги
    'alarms.title':            'Дабылдар',
    'alarms.sound_on':         'Дыбыс: ҚОСУЛЫ',
    'alarms.sound_off':        'Дыбыс: ӨШІРУЛІ',
    'alarms.empty':            'Дабыл жоқ',
    'alarms.resolved_section': 'Шешілген',

    // Карточка тревоги
    'plate.no_plate':    'НӨМІР ЖОҚ',
    'plate.confidence':  'Сенімділік:',
    'plate.in_zone':     'сек. аймақта',
    'plate.show_image':  'Сурет',
    'plate.hide_image':  'Жасыру',
    'plate.resolve':     'Жабу',
    'plate.delete':      'Жою',
    'plate.just_now':    'Жаңа ғана',
    'plate.minutes_ago': 'мин. бұрын',
    'plate.hours_ago':   'сағ. бұрын',
    'plate.days_ago':    'күн бұрын',

    // Зоны
    'zone.title':            'Аймақтар',
    'zone.name_placeholder': 'Аймақ атауы...',
    'zone.save':             'Сақтау',
    'zone.clear':            'Тазалау',
    'zone.drawing_hint':     'Сол жақ басу: нүкте қосу | Оң жақ: болдырмау | Кем дегенде 3 нүкте',
    'zone.empty':            'Аймақ жоқ. Canvas-ке басыңыз.',
    'zone.active':           'Белсенді',
    'zone.inactive':         'Белсенді емес',
    'zone.delete':           'Жою',

    // Статистика
    'stats.total':         'Барлық дабыл',
    'stats.active':        'Белсенді',
    'stats.resolved':      'Шешілген',
    'stats.cpu':           'CPU',
    'stats.camera_fps':    'Камера FPS',
    'stats.system':        'Жүйе',
    'stats.ram':           'RAM',
    'stats.vram':          'VRAM',
    'stats.camera_alarms': 'Камера бойынша дабылдар',
    'stats.hourly_title':  'Сағаттық дабыл бөлінісі (Бүгін)',
    'stats.loading':       'Деректер күтілуде...',
    'stats.no_data':       'Деректер жоқ',

    // Настройки
    'settings.title':              'Камера параметрлері',
    'settings.violation_duration': 'Тыйым салу уақыты',
    'settings.save':               'Сақтау',
    'settings.saved':              '✓ Сақталды',
    'settings.minutes':            'мин.',
    'settings.seconds':            'сек.',
    'settings.camera_section':     'Камера',

    // Фильтр тревог
    'filter.plate':           'Нөмір бойынша іздеу...',
    'filter.all_cameras':     'Барлық камералар',
    'filter.all_status':      'Барлық статус',
    'filter.status_active':   'Белсенді',
    'filter.status_resolved': 'Шешілген',
    'filter.date_from':       'Басталу күні',
    'filter.date_to':         'Аяқталу күні',
    'filter.search':          'Іздеу',
    'filter.reset':           'Тазалау',
    'filter.total':           'Барлығы',
    'filter.prev':            'Алдыңғы',
    'filter.next':            'Келесі',
    'filter.no_results':      'Дабыл табылмады',
    'filter.showing':         'Көрсетілген',

    // Логи
    'logs.title':        'Жүйе журналы',
    'logs.clear':        'Тазалау',
    'logs.auto_scroll':  'Авто-айналдыру',
    'logs.filter_all':   'Барлығы',
    'logs.filter_info':  'INFO',
    'logs.filter_warn':  'WARN',
    'logs.filter_error': 'ERROR',
    'logs.connecting':   'Қосылуда...',
    'logs.no_logs':      'Журнал жазбалары жоқ',
  },
};
