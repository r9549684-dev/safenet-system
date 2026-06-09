// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Persian (`fa`).
class AppLocalizationsFa extends AppLocalizations {
  AppLocalizationsFa([String locale = 'fa']) : super(locale);

  @override
  String get appName => 'سیف‌نت service';

  @override
  String get splashTagline => 'امن. خصوصی. رایگان.';

  @override
  String get chooseLanguage => 'زبان را انتخاب کنید';

  @override
  String get onb1Title => 'سیف‌نت service';

  @override
  String get onb1Sub => 'سانسور اینترنت در امارات، ترکیه و سایر کشورها را دور بزنید — به‌طور نامحسوس.';

  @override
  String get onb2Title => 'فناوری استیلث';

  @override
  String get onb2Sub => 'ByeDPI و AmneziaWG به‌طور خودکار با اینترنت شما سازگار می‌شوند.';

  @override
  String get onb3Title => '۳ روز رایگان';

  @override
  String get onb3Sub => 'همین الان امکانات پریمیوم را امتحان کنید. نیازی به ثبت‌نام نیست.';

  @override
  String get next => 'بعدی →';

  @override
  String get start => 'شروع';

  @override
  String get statusSecureActive => 'تونل امن فعال است';

  @override
  String get statusOffline => 'آفلاین';

  @override
  String get btnConnect => 'اتصال';

  @override
  String get btnDisconnect => 'قطع اتصال';

  @override
  String get btnConnecting => 'در حال اتصال';

  @override
  String get btnStopping => 'در حال قطع';

  @override
  String get btnRetry => 'تلاش مجدد';

  @override
  String get badgePremium => 'پریمیوم ✓';

  @override
  String badgeTrial(int days) {
    return 'آزمایشی: $days روز';
  }

  @override
  String get badgeExpired => 'منقضی شده';

  @override
  String get removeLimit => '💎 حذف محدودیت — پریمیوم';

  @override
  String get bypassModeLabel => 'حالت دور زدن';

  @override
  String get modeStealthLabel => 'خودکار';

  @override
  String get modeStealthDesc => 'انتخاب هوشمند';

  @override
  String get modeByedpiLabel => 'دور زدن';

  @override
  String get modeByedpiDesc => 'شبکه‌های اجتماعی';

  @override
  String get modeAmneziaLabel => 'تونل';

  @override
  String get modeAmneziaDesc => 'حفاظت کامل';

  @override
  String get modeHybridLabel => 'حداکثر';

  @override
  String get modeHybridDesc => 'همه چیز';

  @override
  String get statsDownload => 'دریافت';

  @override
  String get statsUpload => 'ارسال';

  @override
  String get statsPing => 'پینگ';

  @override
  String get trialLastDay => '🔴 آخرین روز آزمایشی!';

  @override
  String get trialExpiredBanner => '🔴 آزمایشی منقضی شد!';

  @override
  String trialFewDays(int days) {
    return '🟡 $days روز آزمایشی باقی مانده';
  }

  @override
  String trialManyDays(int days) {
    return '⏳ آزمایشی: $days روز';
  }

  @override
  String get trialActiveDesc => 'در دوره آزمایشی: نامحدود مثل پریمیوم';

  @override
  String get trialExpiredDesc => 'بعد از آزمایشی: جلسات ۵ دقیقه‌ای';

  @override
  String get upgradeToPremium => 'ارتقا به پریمیوم →';

  @override
  String get premiumTitle => 'سیف‌نت پریمیوم';

  @override
  String get premiumSubtitle => 'دسترسی نامحدود به تمام فناوری‌ها';

  @override
  String get colTrial => 'آزمایشی';

  @override
  String get colPremium => 'پریمیوم';

  @override
  String get featureSessionLen => 'مدت جلسه';

  @override
  String get featureSessionTrialVal => '۳ روز نامحدود';

  @override
  String get featureSessionPremiumVal => 'نامحدود ♾';

  @override
  String get featureAutoConnect => 'اتصال خودکار';

  @override
  String get featureKillSwitch => 'کیل سوئیچ';

  @override
  String get featureBypassModes => 'حالت‌های دور زدن';

  @override
  String get featureAll4 => 'همه ۴';

  @override
  String get featureServers => 'سرورها';

  @override
  String get featureServersTrialVal => 'پایه';

  @override
  String get featureServersPremiumVal => 'همه کشورها';

  @override
  String get featurePrioritySupport => 'پشتیبانی ویژه';

  @override
  String get trialExpiredMsg => 'دوره آزمایشی منقضی شد — جلسات ۵ دقیقه‌ای در دسترس است.';

  @override
  String trialExpiresIn(int days) {
    return 'دوره آزمایشی در $days روز دیگر تمام می‌شود. تا آن زمان — پریمیوم کامل.';
  }

  @override
  String get choosePlan => 'انتخاب طرح';

  @override
  String get plan1w => '۱ هفته';

  @override
  String get plan1m => '۱ ماه';

  @override
  String get plan3m => '۳ ماه';

  @override
  String get plan12m => '۱۲ ماه';

  @override
  String get badgeBestPrice => '🔥 بهترین قیمت';

  @override
  String savingsLabel(String percent) {
    return 'صرفه‌جویی $percent';
  }

  @override
  String get payWithCryptobot => 'پرداخت با کریپتوبات';

  @override
  String get safePayment => 'پرداخت امن • فعال‌سازی فوری';

  @override
  String get paymentDesc => 'پرداخت با USDT TRC20/TON از طریق کریپتوبات';

  @override
  String get sheetSubtitle => 'نامحدود · همه سرورها · اتصال خودکار';

  @override
  String get continueFree => 'ادامه رایگان →';

  @override
  String get settingsTitle => 'تنظیمات';

  @override
  String get sectionAccount => 'حساب کاربری';

  @override
  String get deviceIdLabel => 'شناسه دستگاه';

  @override
  String get expiryLabel => 'انقضا';

  @override
  String get sectionVpn => 'تنظیمات service';

  @override
  String get killSwitchDesc => 'آی‌پی شما هنگام قطع اتصال لو نمی‌رود';

  @override
  String get autoConnectLabel => 'اتصال خودکار';

  @override
  String get autoConnectDesc => 'هنگام راه‌اندازی برنامه';

  @override
  String get resetSettings => 'بازگشت به تنظیمات اولیه';

  @override
  String get resetDialogTitle => 'از نو شروع کنیم؟';

  @override
  String get resetDialogContent => 'همه چیز از ابتدا شروع می‌شود.';

  @override
  String get cancel => 'لغو';

  @override
  String get confirm => 'تأیید';

  @override
  String get affiliateNavTitle => 'برنامه شریک';

  @override
  String get affiliateNavSubtitle => 'درآمد از زیرمجموعه‌ها';

  @override
  String get navHome => 'خانه';

  @override
  String get navServers => 'سرورها';

  @override
  String get navPremium => 'پریمیوم';

  @override
  String get navOptions => 'گزینه‌ها';

  @override
  String get affiliateAppBarTitle => 'برنامه معرفی';

  @override
  String get walletSaved => 'کیف پول ذخیره شد';

  @override
  String get withdrawalCreated => 'درخواست برداشت ایجاد شد';

  @override
  String get partnerActivated => 'وضعیت شریک فعال شد!';

  @override
  String get error => 'خطا';

  @override
  String get statsTitle => 'آمار';

  @override
  String get referrals => 'زیرمجموعه‌ها';

  @override
  String get rate => 'نرخ';

  @override
  String get discount => 'تخفیف';

  @override
  String get connectFriend => 'دوست بیاور';

  @override
  String get typeBadgePartner => 'شریک';

  @override
  String get typeBadgeUser => 'کاربر';

  @override
  String get refCodeTitle => 'کد معرف';

  @override
  String get codeCopied => 'کد کپی شد';

  @override
  String get discountCardTitle => 'service با ۵۰٪ تخفیف';

  @override
  String get discountCardHeader => '👥 دوست بیاور';

  @override
  String get discountCardDesc => '۱ تا ۱۰ دوست بیاور — برای هر زیرمجموعه پرداخت‌کننده ۵۰٪ تخفیف در پرداخت بعدی دریافت کن.';

  @override
  String get discountCardNote => '۱ — ۱۰ دوست = ۵۰٪ تخفیف برای هر کدام';

  @override
  String get discountCardInfo => 'دوست QR را اسکن می‌کند یا کد را هنگام نصب وارد می‌کند — تخفیف خودکار اعمال می‌شود';

  @override
  String get partnerTiersTitle => 'تبدیل به شریک شوید';

  @override
  String get partnerTiersSubtitle => 'از ۱۱ زیرمجموعه پرداخت‌کننده — درآمد واقعی در TON';

  @override
  String get tierColReferrals => 'زیرمجموعه‌ها';

  @override
  String get tierColFirstPay => 'اولین پرداخت';

  @override
  String get tierColMonthly => 'ماهانه';

  @override
  String get tierNoteText => '\$1.5 — یک‌بار در اولین پرداخت زیرمجموعه\n% — ماهانه از هر پرداخت بعدی';

  @override
  String get qrTitle => '📲 کد QR برای دوستان';

  @override
  String get qrSubtitle => 'اسکن کرد — دانلود کرد — کد شما از قبل ثبت شده';

  @override
  String get copyLink => 'کپی لینک';

  @override
  String get linkCopied => 'لینک کپی شد';

  @override
  String get walletTitle => '💼 کیف پول TON';

  @override
  String get saveBtn => 'ذخیره';

  @override
  String get balanceTitle => '💸 موجودی';

  @override
  String balanceMin(String ton) {
    return 'حداقل: $ton TON (~\$5)';
  }

  @override
  String get withdrawAmount => 'مقدار TON';

  @override
  String get withdrawBtn => 'برداشت';

  @override
  String get insufficientFunds => 'موجودی کافی برای برداشت وجود ندارد';

  @override
  String get becomePartnerTitle => '🚀 تبدیل به شریک شوید';

  @override
  String get becomePartnerDesc => 'از ۱۱ زیرمجموعه پرداخت‌کننده در دسترس است. پرداخت به کیف پول TON.';

  @override
  String get walletHint => '0:abc... یا EQabc...';

  @override
  String get walletForPayouts => 'کیف پول TON برای پرداخت‌ها';

  @override
  String get applyBtn => 'ثبت درخواست';

  @override
  String get withdrawHistoryTitle => '📋 تاریخچه برداشت‌ها';

  @override
  String get promoCodeHint => 'کد تخفیف';

  @override
  String get promoCodeApply => 'اعمال';

  @override
  String promoCodeSuccess(int months) {
    return '✓ پریمیوم برای $months ماه فعال شد!';
  }

  @override
  String get linkTelegramBtn => '🔗 اتصال به تلگرام';

  @override
  String get promoCodeLabel => 'کد تخفیف دارید?';

  @override
  String get serversTitle => 'سرورها';

  @override
  String get searchCountry => 'جستجوی کشور...';

  @override
  String get autoSelectLabel => 'انتخاب خودکار';

  @override
  String get fastestServer => 'سریع‌ترین سرور';

  @override
  String get supportNavTitle => 'پشتیبانی';

  @override
  String get supportNavSubtitle => 'سؤالات متداول · هوش مصنوعی';

  @override
  String get supportTitle => 'پشتیبانی';

  @override
  String get supportSubtitle => 'سؤالات متداول، هوش مصنوعی و پشتیبانی تلگرام';

  @override
  String get supportTelegramTitle => 'تماس با پشتیبانی از طریق تلگرام';

  @override
  String get supportTelegramDesc => 'تلگرام · پاسخ سریع';

  @override
  String get supportFaqTitle => 'سؤالات متداول';

  @override
  String get supportFaqDesc => 'پاسخ به سؤالات رایج';

  @override
  String get supportAiTitle => 'دستیار هوش مصنوعی';

  @override
  String get supportAiDesc => 'دستیار هوشمند در تلگرام';

  @override
  String get supportComingSoon => 'به زودی';

  @override
  String get homeEarnTitle => 'با ما کسب درآمد کنید';

  @override
  String get homeEarnSubtitle => 'درآمد اضافی از مشترکین شما!';

  @override
  String get homeInviteTitle => '👥 دوست دعوت کن — نصف قیمت بپرداز';

  @override
  String get sectionServer => 'پروفایل service';

  @override
  String get serverCardDesc => 'برای تغییر سرور ضربه بزنید';

  @override
  String get updateTitle => 'بروزرسانی موجود است';

  @override
  String updateMsg(String version) {
    return 'نسخه $version در دسترس است. برای ویژگی‌های جدید بروزرسانی کنید.';
  }

  @override
  String get updateBtn => 'بروزرسانی';

  @override
  String get updateLater => 'بعداً';
}
