export type Lang = 'ru' | 'kk' | 'en';

export type TranslationKey =
  // Навигация
  | 'nav.live' | 'nav.alarms' | 'nav.zones' | 'nav.settings'
  | 'nav.logs' | 'nav.plates' | 'nav.gallery' | 'nav.penalties'
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
  | 'logs.connecting' | 'logs.no_logs'
  // Штрафы / Penalties
  | 'penalty.title' | 'penalty.subtitle'
  | 'penalty.card_pending' | 'penalty.card_sent' | 'penalty.card_cancelled'
  | 'penalty.send_all' | 'penalty.sending_all'
  | 'penalty.filter_all' | 'penalty.filter_pending' | 'penalty.filter_sent' | 'penalty.filter_cancelled'
  | 'penalty.search_placeholder' | 'penalty.refresh'
  | 'penalty.total' | 'penalty.records'
  | 'penalty.empty' | 'penalty.empty_sub' | 'penalty.loading'
  | 'penalty.col_plate' | 'penalty.col_camera' | 'penalty.col_duration'
  | 'penalty.col_amount' | 'penalty.col_status' | 'penalty.col_date' | 'penalty.col_action'
  | 'penalty.btn_send' | 'penalty.btn_cancel' | 'penalty.btn_send_fine'
  | 'penalty.prev' | 'penalty.next'
  | 'penalty.info_title' | 'penalty.info_mock'
  | 'penalty.status_pending' | 'penalty.status_sent' | 'penalty.status_cancelled'
  | 'penalty.camera'
  // Camera Health Monitor
  | 'health.title'
  | 'health.ws_connected' | 'health.ws_connecting' | 'health.ws_disconnected'
  | 'health.no_cameras' | 'health.waiting_ws'
  | 'health.fps_label' | 'health.fps_good' | 'health.fps_medium' | 'health.fps_low'
  | 'health.online' | 'health.offline'
  | 'health.connection' | 'health.stable' | 'health.no_signal'
  | 'health.night_mode' | 'health.night_active' | 'health.night_off'
  | 'health.system_resources'
  // Whitelist
  | 'wl.title' | 'wl.entries_count'
  | 'wl.add_title' | 'wl.plate_label' | 'wl.reason_label'
  | 'wl.adding' | 'wl.add_btn' | 'wl.loading'
  | 'wl.empty' | 'wl.empty_sub'
  | 'wl.col_plate' | 'wl.col_reason' | 'wl.col_date' | 'wl.col_action'
  | 'wl.enter_plate'
  | 'wl.reason_staff' | 'wl.reason_disabled' | 'wl.reason_vip'
  | 'wl.reason_special' | 'wl.reason_other';

type Translations = Record<TranslationKey, string>;

export const translations: Record<Lang, Translations> = {
  // ═══════════════════════════════════════════════════
  //  РУССКИЙ
  // ═══════════════════════════════════════════════════
  ru: {
    // Навигация
    'nav.live':      'Прямой эфир',
    'nav.alarms':    'Тревоги',
    'nav.zones':     'Зоны',
    'nav.settings':  'Настройки',
    'nav.logs':      'Логи',
    'nav.plates':    'Номера',
    'nav.gallery':   'Галерея',
    'nav.penalties': 'Штрафы',

    // Камеры
    'camera.1': 'Въезд',
    'camera.2': 'Парковка-А',
    'camera.3': 'Парковка-Б',

    // Видео
    'video.connecting':   'Подключение...',
    'video.no_signal':    'Нет сигнала',
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
    'zone.title':            'Зоны',
    'zone.name_placeholder': 'Название зоны...',
    'zone.save':             'Сохранить',
    'zone.clear':            'Очистить',
    'zone.drawing_hint':     'Лев. клик: точка | Прав. клик: отменить | Мин. 3 точки',
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

    // Штрафы
    'penalty.title':             'Штрафы',
    'penalty.subtitle':          'Нарушения с распознанными номерами автоматически попадают в очередь',
    'penalty.card_pending':      'Ожидающие',
    'penalty.card_sent':         'Отправленные',
    'penalty.card_cancelled':    'Отменённые',
    'penalty.send_all':          'Отправить все',
    'penalty.sending_all':       'Отправка...',
    'penalty.filter_all':        'Все',
    'penalty.filter_pending':    'Ожидающие',
    'penalty.filter_sent':       'Отправленные',
    'penalty.filter_cancelled':  'Отменённые',
    'penalty.search_placeholder':'Поиск по номеру...',
    'penalty.refresh':           'Обновить',
    'penalty.total':             'Итого',
    'penalty.records':           'записей',
    'penalty.empty':             'Штрафов не найдено',
    'penalty.empty_sub':         'Нарушения с номерами появятся здесь автоматически',
    'penalty.loading':           'Загрузка...',
    'penalty.col_plate':         'Номер',
    'penalty.col_camera':        'Камера / Зона',
    'penalty.col_duration':      'Длительность',
    'penalty.col_amount':        'Штраф (₸)',
    'penalty.col_status':        'Статус',
    'penalty.col_date':          'Дата',
    'penalty.col_action':        'Действие',
    'penalty.btn_send':          'Отправить',
    'penalty.btn_cancel':        'Отмена',
    'penalty.btn_send_fine':     '💸 Штраф',
    'penalty.prev':              '← Назад',
    'penalty.next':              'Вперёд →',
    'penalty.info_title':        'Расчёт штрафов (КоАП Ст. 462)',
    'penalty.info_mock':         'Для реальной отправки требуется интеграция с e-gov API. Сейчас работает в режиме демо.',
    'penalty.status_pending':    '⏳ Ожидает',
    'penalty.status_sent':       '✅ Отправлен',
    'penalty.status_cancelled':  '✖ Отменён',
    'penalty.camera':            'Камера',

    // Camera Health
    'health.title':           'Мониторинг камер',
    'health.ws_connected':    'WebSocket подключён',
    'health.ws_connecting':   'Подключение...',
    'health.ws_disconnected': 'Отключён',
    'health.no_cameras':      'Нет данных о камерах',
    'health.waiting_ws':      'Ожидание данных от WebSocket...',
    'health.fps_label':       'Частота кадров',
    'health.fps_good':        'Отлично',
    'health.fps_medium':      'Средне',
    'health.fps_low':         'Низко',
    'health.online':          'Онлайн',
    'health.offline':         'Оффлайн',
    'health.connection':      'Подключение',
    'health.stable':          'Стабильное',
    'health.no_signal':       'Нет связи',
    'health.night_mode':      'Ночной режим',
    'health.night_active':    'Активен',
    'health.night_off':       'Выключен',
    'health.system_resources':'Системные ресурсы',

    // Whitelist
    'wl.title':        'Белый список',
    'wl.entries_count':'записей',
    'wl.add_title':    'Добавить номер',
    'wl.plate_label':  'Гос. номер',
    'wl.reason_label': 'Причина',
    'wl.adding':       'Добавление...',
    'wl.add_btn':      'Добавить',
    'wl.loading':      'Загрузка...',
    'wl.empty':        'Белый список пуст',
    'wl.empty_sub':    'Добавьте номера, которые не должны вызывать тревоги',
    'wl.col_plate':    'Номер',
    'wl.col_reason':   'Причина',
    'wl.col_date':     'Дата добавления',
    'wl.col_action':   'Действие',
    'wl.enter_plate':  'Введите номер',
    'wl.reason_staff':   'Персонал',
    'wl.reason_disabled':'Инвалид',
    'wl.reason_vip':     'VIP',
    'wl.reason_special': 'Спецтранспорт',
    'wl.reason_other':   'Другое',
  },

  // ═══════════════════════════════════════════════════
  //  ҚАЗАҚША
  // ═══════════════════════════════════════════════════
  kk: {
    // Навигация
    'nav.live':      'Тікелей трансляция',
    'nav.alarms':    'Дабылдар',
    'nav.zones':     'Аймақтар',
    'nav.settings':  'Параметрлер',
    'nav.logs':      'Журнал',
    'nav.plates':    'Нөмірлер',
    'nav.gallery':   'Галерея',
    'nav.penalties': 'Айыппұлдар',

    // Камеры
    'camera.1': 'Кіріс есігі',
    'camera.2': 'Автотұрақ-А',
    'camera.3': 'Автотұрақ-Б',

    // Видео
    'video.connecting':   'Қосылуда...',
    'video.no_signal':    'Байланыс жоқ',
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
    'zone.drawing_hint':     'Сол жақ: нүкте қосу | Оң жақ: болдырмау | Кем дегенде 3 нүкте',
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

    // Айыппұлдар
    'penalty.title':             'Айыппұлдар',
    'penalty.subtitle':          'Анықталған нөмірі бар бұзушылықтар автоматты түрде кезекке қосылады',
    'penalty.card_pending':      'Күтіп тұрған',
    'penalty.card_sent':         'Жіберілген',
    'penalty.card_cancelled':    'Болдырылмаған',
    'penalty.send_all':          'Барлығын жіберу',
    'penalty.sending_all':       'Жіберілуде...',
    'penalty.filter_all':        'Барлығы',
    'penalty.filter_pending':    'Күтіп тұрған',
    'penalty.filter_sent':       'Жіберілген',
    'penalty.filter_cancelled':  'Болдырылмаған',
    'penalty.search_placeholder':'Нөмір бойынша іздеу...',
    'penalty.refresh':           'Жаңарту',
    'penalty.total':             'Барлығы',
    'penalty.records':           'жазба',
    'penalty.empty':             'Айыппұл табылмады',
    'penalty.empty_sub':         'Нөмірі анықталған бұзушылықтар мұнда автоматты пайда болады',
    'penalty.loading':           'Жүктелуде...',
    'penalty.col_plate':         'Нөмір',
    'penalty.col_camera':        'Камера / Аймақ',
    'penalty.col_duration':      'Ұзақтығы',
    'penalty.col_amount':        'Айыппұл (₸)',
    'penalty.col_status':        'Статус',
    'penalty.col_date':          'Күні',
    'penalty.col_action':        'Әрекет',
    'penalty.btn_send':          'Жіберу',
    'penalty.btn_cancel':        'Болдырмау',
    'penalty.btn_send_fine':     '💸 Айыппұл',
    'penalty.prev':              '← Алдыңғы',
    'penalty.next':              'Келесі →',
    'penalty.info_title':        'Айыппұл есебі (ӘҚБК 462-бап)',
    'penalty.info_mock':         'Нақты жіберу үшін e-gov API интеграциясы қажет. Қазір демо режимінде жұмыс істейді.',
    'penalty.status_pending':    '⏳ Күтуде',
    'penalty.status_sent':       '✅ Жіберілді',
    'penalty.status_cancelled':  '✖ Болдырылмады',
    'penalty.camera':            'Камера',

    // Camera Health
    'health.title':           'Камера мониторингі',
    'health.ws_connected':    'WebSocket қосылды',
    'health.ws_connecting':   'Қосылуда...',
    'health.ws_disconnected': 'Ажыратылды',
    'health.no_cameras':      'Камера туралы деректер жоқ',
    'health.waiting_ws':      'WebSocket деректерін күту...',
    'health.fps_label':       'Кадр жиілігі',
    'health.fps_good':        'Тамаша',
    'health.fps_medium':      'Орташа',
    'health.fps_low':         'Төмен',
    'health.online':          'Онлайн',
    'health.offline':         'Оффлайн',
    'health.connection':      'Қосылым',
    'health.stable':          'Тұрақты',
    'health.no_signal':       'Байланыс жоқ',
    'health.night_mode':      'Түнгі режим',
    'health.night_active':    'Белсенді',
    'health.night_off':       'Өшірулі',
    'health.system_resources':'Жүйе ресурстары',

    // Whitelist
    'wl.title':        'Ақ тізім',
    'wl.entries_count':'жазба',
    'wl.add_title':    'Нөмір қосу',
    'wl.plate_label':  'Мем. нөмір',
    'wl.reason_label': 'Себебі',
    'wl.adding':       'Қосылуда...',
    'wl.add_btn':      'Қосу',
    'wl.loading':      'Жүктелуде...',
    'wl.empty':        'Ақ тізім бос',
    'wl.empty_sub':    'Дабыл тудырмайтын нөмірлерді қосыңыз',
    'wl.col_plate':    'Нөмір',
    'wl.col_reason':   'Себебі',
    'wl.col_date':     'Қосылған күні',
    'wl.col_action':   'Әрекет',
    'wl.enter_plate':  'Нөмірді енгізіңіз',
    'wl.reason_staff':   'Персонал',
    'wl.reason_disabled':'Мүгедек',
    'wl.reason_vip':     'VIP',
    'wl.reason_special': 'Арнайы көлік',
    'wl.reason_other':   'Басқа',
  },

  // ═══════════════════════════════════════════════════
  //  ENGLISH
  // ═══════════════════════════════════════════════════
  en: {
    // Navigation
    'nav.live':      'Live Feed',
    'nav.alarms':    'Alarms',
    'nav.zones':     'Zones',
    'nav.settings':  'Settings',
    'nav.logs':      'Logs',
    'nav.plates':    'Plates',
    'nav.gallery':   'Gallery',
    'nav.penalties': 'Fines',

    // Cameras
    'camera.1': 'Entrance',
    'camera.2': 'Parking-A',
    'camera.3': 'Parking-B',

    // Video
    'video.connecting':   'Connecting...',
    'video.no_signal':    'No Signal',
    'video.back_to_grid': 'Back to Grid',

    // Alarms
    'alarms.title':            'Alarms',
    'alarms.sound_on':         'Sound: ON',
    'alarms.sound_off':        'Sound: OFF',
    'alarms.empty':            'No alarms yet',
    'alarms.resolved_section': 'Resolved',

    // Alarm card
    'plate.no_plate':    'NO PLATE',
    'plate.confidence':  'Confidence:',
    'plate.in_zone':     'sec. in zone',
    'plate.show_image':  'Photo',
    'plate.hide_image':  'Hide',
    'plate.resolve':     'Resolve',
    'plate.delete':      'Delete',
    'plate.just_now':    'Just now',
    'plate.minutes_ago': 'min. ago',
    'plate.hours_ago':   'hr. ago',
    'plate.days_ago':    'd. ago',

    // Zones
    'zone.title':            'Zones',
    'zone.name_placeholder': 'Zone name...',
    'zone.save':             'Save',
    'zone.clear':            'Clear',
    'zone.drawing_hint':     'Left click: add point | Right click: cancel | Min. 3 points',
    'zone.empty':            'No zones. Click on canvas.',
    'zone.active':           'Active',
    'zone.inactive':         'Inactive',
    'zone.delete':           'Delete',

    // Statistics
    'stats.total':         'Total alarms',
    'stats.active':        'Active',
    'stats.resolved':      'Resolved',
    'stats.cpu':           'CPU',
    'stats.camera_fps':    'Camera FPS',
    'stats.system':        'System',
    'stats.ram':           'RAM',
    'stats.vram':          'VRAM',
    'stats.camera_alarms': 'Alarms by camera',
    'stats.hourly_title':  'Hourly alarm distribution (Today)',
    'stats.loading':       'Waiting for data...',
    'stats.no_data':       'No data yet',

    // Settings
    'settings.title':              'Camera Settings',
    'settings.violation_duration': 'Violation duration',
    'settings.save':               'Save',
    'settings.saved':              '✓ Saved',
    'settings.minutes':            'min.',
    'settings.seconds':            'sec.',
    'settings.camera_section':     'Camera',

    // Alarm filter
    'filter.plate':           'Search by plate...',
    'filter.all_cameras':     'All cameras',
    'filter.all_status':      'All statuses',
    'filter.status_active':   'Active',
    'filter.status_resolved': 'Resolved',
    'filter.date_from':       'Date from',
    'filter.date_to':         'Date to',
    'filter.search':          'Search',
    'filter.reset':           'Reset',
    'filter.total':           'Total',
    'filter.prev':            'Prev',
    'filter.next':            'Next',
    'filter.no_results':      'No alarms found',
    'filter.showing':         'Showing',

    // Logs
    'logs.title':        'System Logs',
    'logs.clear':        'Clear',
    'logs.auto_scroll':  'Auto-scroll',
    'logs.filter_all':   'All',
    'logs.filter_info':  'INFO',
    'logs.filter_warn':  'WARN',
    'logs.filter_error': 'ERROR',
    'logs.connecting':   'Connecting...',
    'logs.no_logs':      'No logs',

    // Fines / Penalties
    'penalty.title':             'Fines',
    'penalty.subtitle':          'Violations with detected plates are automatically queued',
    'penalty.card_pending':      'Pending Fines',
    'penalty.card_sent':         'Sent Fines',
    'penalty.card_cancelled':    'Cancelled',
    'penalty.send_all':          'Send All',
    'penalty.sending_all':       'Sending...',
    'penalty.filter_all':        'All',
    'penalty.filter_pending':    'Pending',
    'penalty.filter_sent':       'Sent',
    'penalty.filter_cancelled':  'Cancelled',
    'penalty.search_placeholder':'Search plate...',
    'penalty.refresh':           'Refresh',
    'penalty.total':             'Total',
    'penalty.records':           'records',
    'penalty.empty':             'No fines found',
    'penalty.empty_sub':         'Violations with plates will appear here automatically',
    'penalty.loading':           'Loading...',
    'penalty.col_plate':         'Plate',
    'penalty.col_camera':        'Camera / Zone',
    'penalty.col_duration':      'Duration',
    'penalty.col_amount':        'Fine (₸)',
    'penalty.col_status':        'Status',
    'penalty.col_date':          'Date',
    'penalty.col_action':        'Action',
    'penalty.btn_send':          'Send',
    'penalty.btn_cancel':        'Cancel',
    'penalty.btn_send_fine':     '💸 Fine',
    'penalty.prev':              '← Prev',
    'penalty.next':              'Next →',
    'penalty.info_title':        'Fine Calculation (КоАП Art. 462)',
    'penalty.info_mock':         'Real sending requires e-gov API integration. Currently running in demo mode.',
    'penalty.status_pending':    '⏳ Pending',
    'penalty.status_sent':       '✅ Sent',
    'penalty.status_cancelled':  '✖ Cancelled',
    'penalty.camera':            'Camera',

    // Camera Health
    'health.title':           'Camera Monitoring',
    'health.ws_connected':    'WebSocket connected',
    'health.ws_connecting':   'Connecting...',
    'health.ws_disconnected': 'Disconnected',
    'health.no_cameras':      'No camera data',
    'health.waiting_ws':      'Waiting for WebSocket data...',
    'health.fps_label':       'Frame rate',
    'health.fps_good':        'Excellent',
    'health.fps_medium':      'Average',
    'health.fps_low':         'Low',
    'health.online':          'Online',
    'health.offline':         'Offline',
    'health.connection':      'Connection',
    'health.stable':          'Stable',
    'health.no_signal':       'No signal',
    'health.night_mode':      'Night mode',
    'health.night_active':    'Active',
    'health.night_off':       'Off',
    'health.system_resources':'System resources',

    // Whitelist
    'wl.title':        'Whitelist',
    'wl.entries_count':'entries',
    'wl.add_title':    'Add plate',
    'wl.plate_label':  'License plate',
    'wl.reason_label': 'Reason',
    'wl.adding':       'Adding...',
    'wl.add_btn':      'Add',
    'wl.loading':      'Loading...',
    'wl.empty':        'Whitelist is empty',
    'wl.empty_sub':    'Add plates that should not trigger alarms',
    'wl.col_plate':    'Plate',
    'wl.col_reason':   'Reason',
    'wl.col_date':     'Date added',
    'wl.col_action':   'Action',
    'wl.enter_plate':  'Enter plate number',
    'wl.reason_staff':   'Staff',
    'wl.reason_disabled':'Disabled',
    'wl.reason_vip':     'VIP',
    'wl.reason_special': 'Special vehicle',
    'wl.reason_other':   'Other',
  },
};
