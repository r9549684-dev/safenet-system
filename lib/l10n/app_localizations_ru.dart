// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Russian (`ru`).
class AppLocalizationsRu extends AppLocalizations {
  AppLocalizationsRu([String locale = 'ru']) : super(locale);

  @override
  String get appName => 'SafeNet service';

  @override
  String get splashTagline => 'Безопасно. Приватно. Бесплатно.';

  @override
  String get chooseLanguage => 'Выберите язык';

  @override
  String get onb1Title => 'SafeNet service';

  @override
  String get onb1Sub => 'Обходите цензуру в ОАЭ, Турции и других странах — незаметно.';

  @override
  String get onb2Title => 'Stealth Технологии';

  @override
  String get onb2Sub => 'ByeDPI и AmneziaWG автоматически подстраиваются под провайдера.';

  @override
  String get onb3Title => '3 Дня Бесплатно';

  @override
  String get onb3Sub => 'Попробуйте премиум функции прямо сейчас. Регистрация не нужна.';

  @override
  String get next => 'Далее →';

  @override
  String get start => 'Начать';

  @override
  String get statusSecureActive => 'Secure Tunnel Active';

  @override
  String get statusOffline => 'Offline';

  @override
  String get btnConnect => 'CONNECT';

  @override
  String get btnDisconnect => 'DISCONNECT';

  @override
  String get btnConnecting => 'CONNECTING';

  @override
  String get btnStopping => 'STOPPING';

  @override
  String get btnRetry => 'RETRY';

  @override
  String get badgePremium => 'PREMIUM ✓';

  @override
  String badgeTrial(int days) {
    return 'ТРИАЛ: $days ДНЕЙ';
  }

  @override
  String get badgeExpired => 'ИСТЁК';

  @override
  String get removeLimit => '💎 Убрать ограничение — Premium';

  @override
  String get bypassModeLabel => 'РЕЖИМ ОБХОДА';

  @override
  String get modeStealthLabel => 'Авто';

  @override
  String get modeStealthDesc => 'Умный выбор';

  @override
  String get modeByedpiLabel => 'Обход';

  @override
  String get modeByedpiDesc => 'Соцсети, аппы';

  @override
  String get modeAmneziaLabel => 'Туннель';

  @override
  String get modeAmneziaDesc => 'Полная защита';

  @override
  String get modeHybridLabel => 'Максимум';

  @override
  String get modeHybridDesc => 'Всё сразу';

  @override
  String get statsDownload => 'Загрузка';

  @override
  String get statsUpload => 'Отдача';

  @override
  String get statsPing => 'Пинг';

  @override
  String get trialLastDay => '🔴 Последний день триала!';

  @override
  String get trialExpiredBanner => '🔴 Триал окончен!';

  @override
  String trialFewDays(int days) {
    return '🟡 Осталось $days дня триала';
  }

  @override
  String trialManyDays(int days) {
    return '⏳ Триал: $days дней';
  }

  @override
  String get trialActiveDesc => 'Во время триала: безлимит как Premium';

  @override
  String get trialExpiredDesc => 'После триала: сессии по 5 минут';

  @override
  String get upgradeToPremium => 'Перейти на Premium →';

  @override
  String get premiumTitle => 'SafeNet Premium';

  @override
  String get premiumSubtitle => 'Безлимитный доступ ко всем технологиям';

  @override
  String get colTrial => 'ТРИАЛ';

  @override
  String get colPremium => 'PREMIUM';

  @override
  String get featureSessionLen => 'Длительность сессии';

  @override
  String get featureSessionTrialVal => '3 дня безлимит';

  @override
  String get featureSessionPremiumVal => 'Безлимит ♾';

  @override
  String get featureAutoConnect => 'Авто-подключение';

  @override
  String get featureKillSwitch => 'Kill Switch';

  @override
  String get featureBypassModes => 'Режимы обхода';

  @override
  String get featureAll4 => 'Все 4';

  @override
  String get featureServers => 'Серверы';

  @override
  String get featureServersTrialVal => 'Базовые';

  @override
  String get featureServersPremiumVal => 'Все страны';

  @override
  String get featurePrioritySupport => 'Приоритет поддержки';

  @override
  String get trialExpiredMsg => 'Триал истёк — доступны сессии по 5 минут.';

  @override
  String trialExpiresIn(int days) {
    return 'Триал заканчивается через $days дней. Пока действует — полный Premium.';
  }

  @override
  String get choosePlan => 'ВЫБЕРИТЕ ПЛАН';

  @override
  String get plan1w => '1 Неделя';

  @override
  String get plan1m => '1 Месяц';

  @override
  String get plan3m => '3 Месяца';

  @override
  String get plan12m => '12 Месяцев';

  @override
  String get badgeBestPrice => '🔥 ЛУЧШАЯ ЦЕНА';

  @override
  String savingsLabel(String percent) {
    return 'Экономия $percent';
  }

  @override
  String get payWithCryptobot => 'Оплатить в CryptoBot';

  @override
  String get safePayment => 'БЕЗОПАСНАЯ ОПЛАТА • АКТИВАЦИЯ МГНОВЕННО';

  @override
  String get paymentDesc => 'Оплата в USDT TRC20/TON через CryptoBot';

  @override
  String get sheetSubtitle => 'Безлимит · Все серверы · Авто-подключение';

  @override
  String get continueFree => 'Продолжить бесплатно →';

  @override
  String get settingsTitle => 'Настройки';

  @override
  String get sectionAccount => 'Аккаунт';

  @override
  String get deviceIdLabel => 'ID Устройства';

  @override
  String get expiryLabel => 'Истекает';

  @override
  String get sectionVpn => 'service Параметры';

  @override
  String get killSwitchDesc => 'Твой IP не засветится при обрыве';

  @override
  String get autoConnectLabel => 'Авто-подключение';

  @override
  String get autoConnectDesc => 'При запуске приложения';

  @override
  String get resetSettings => 'Вернуться к первоначальным настройкам';

  @override
  String get resetDialogTitle => 'Начнём сначала?';

  @override
  String get resetDialogContent => 'Все начнется заново.';

  @override
  String get cancel => 'Отмена';

  @override
  String get confirm => 'Подтвердить';

  @override
  String get affiliateNavTitle => 'Партнёрская программа';

  @override
  String get affiliateNavSubtitle => 'Зарабатывай на рефералах';

  @override
  String get navHome => 'Главная';

  @override
  String get navServers => 'Серверы';

  @override
  String get navPremium => 'Премиум';

  @override
  String get navOptions => 'Опции';

  @override
  String get affiliateAppBarTitle => 'Реферальная программа';

  @override
  String get walletSaved => 'Кошелёк сохранён';

  @override
  String get withdrawalCreated => 'Запрос на вывод создан';

  @override
  String get partnerActivated => 'Статус партнёра активирован!';

  @override
  String get error => 'Ошибка';

  @override
  String get statsTitle => 'Статистика';

  @override
  String get referrals => 'Рефералов';

  @override
  String get rate => 'Ставка';

  @override
  String get discount => 'Скидка';

  @override
  String get connectFriend => 'Подключи друга';

  @override
  String get typeBadgePartner => 'ПАРТНЁР';

  @override
  String get typeBadgeUser => 'ПОЛЬЗОВАТЕЛЬ';

  @override
  String get refCodeTitle => 'Реферальный код';

  @override
  String get codeCopied => 'Код скопирован';

  @override
  String get discountCardTitle => 'сервис за 50% цены';

  @override
  String get discountCardHeader => '👥 Подключи друга';

  @override
  String get discountCardDesc => 'Приведи от 1 до 10 друзей — получи скидку 50% на следующую оплату за каждого платящего реферала.';

  @override
  String get discountCardNote => '1 — 10 друзей = 50% скидка за каждого';

  @override
  String get discountCardInfo => 'Друг сканирует QR или вводит код при установке — скидка применяется автоматически';

  @override
  String get partnerTiersTitle => 'Стать партнёром';

  @override
  String get partnerTiersSubtitle => 'От 11 платящих рефералов — реальный доход на TON';

  @override
  String get tierColReferrals => 'Рефералов';

  @override
  String get tierColFirstPay => 'При 1-й оплате';

  @override
  String get tierColMonthly => 'Ежемесячно';

  @override
  String get tierNoteText => '\$1.5 — единовременно при первой оплате реферала\n% — ежемесячно от каждой последующей оплаты';

  @override
  String get qrTitle => '📲 QR-код для друзей';

  @override
  String get qrSubtitle => 'Отсканировал — скачал — твой код уже привязан';

  @override
  String get copyLink => 'Скопировать ссылку';

  @override
  String get linkCopied => 'Ссылка скопирована';

  @override
  String get walletTitle => '💼 TON Кошелёк';

  @override
  String get saveBtn => 'Сохранить';

  @override
  String get balanceTitle => '💸 Баланс';

  @override
  String balanceMin(String ton) {
    return 'Минимум: $ton TON (~\$5)';
  }

  @override
  String get withdrawAmount => 'Сумма TON';

  @override
  String get withdrawBtn => 'Вывести';

  @override
  String get insufficientFunds => 'Недостаточно средств для вывода';

  @override
  String get becomePartnerTitle => '🚀 Стать партнёром';

  @override
  String get becomePartnerDesc => 'Доступно от 11 платящих рефералов. Выплаты на TON-кошелёк.';

  @override
  String get walletHint => '0:abc... или EQabc...';

  @override
  String get walletForPayouts => 'TON кошелёк для выплат';

  @override
  String get applyBtn => 'Подать заявку';

  @override
  String get withdrawHistoryTitle => '📋 История выводов';

  @override
  String get promoCodeHint => 'Промокод';

  @override
  String get promoCodeApply => 'Применить';

  @override
  String promoCodeSuccess(int months) {
    return '✓ Premium на $months мес.активирован!';
  }

  @override
  String get linkTelegramBtn => '🔗 Привязать Telegram';

  @override
  String get promoCodeLabel => 'Есть промокод?';

  @override
  String get serversTitle => 'Серверы';

  @override
  String get searchCountry => 'Поиск страны...';

  @override
  String get autoSelectLabel => 'Авто-выбор';

  @override
  String get fastestServer => 'Самый быстрый сервер';

  @override
  String get supportNavTitle => 'Техподдержка';

  @override
  String get supportNavSubtitle => 'FAQ · AI-агент';

  @override
  String get supportTitle => 'Техподдержка';

  @override
  String get supportSubtitle => 'FAQ, AI-агент и поддержка в Telegram';

  @override
  String get supportTelegramTitle => 'Написать в поддержку через Telegram';

  @override
  String get supportTelegramDesc => 'Telegram · Ответим быстро';

  @override
  String get supportFaqTitle => 'Часто задаваемые вопросы';

  @override
  String get supportFaqDesc => 'Ответы на популярные вопросы';

  @override
  String get supportAiTitle => 'AI-агент поддержки';

  @override
  String get supportAiDesc => 'Умный помощник в Telegram';

  @override
  String get supportComingSoon => 'СКОРО';

  @override
  String get homeEarnTitle => 'Зарабатывай с нами';

  @override
  String get homeEarnSubtitle => 'Дополнительный доход с твоих подписчиков!';

  @override
  String get homeInviteTitle => '👥 Подключи друга — плати полцены';

  @override
  String get sectionServer => 'ПРОФИЛЬ service';

  @override
  String get serverCardDesc => 'Нажмите чтобы сменить сервер';

  @override
  String get updateTitle => 'Доступно обновление';

  @override
  String updateMsg(String version) {
    return 'Версия $version доступна. Обновите для новых функций.';
  }

  @override
  String get updateBtn => 'Обновить';

  @override
  String get updateLater => 'Позже';
}
