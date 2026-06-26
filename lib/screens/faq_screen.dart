import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';

class FaqScreen extends StatelessWidget {
  const FaqScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final locale = Localizations.localeOf(context).languageCode;
    final faq = _faqData(locale);

    return Scaffold(
      backgroundColor: AppTheme.bg,
      appBar: AppBar(
        backgroundColor: AppTheme.bg,
        elevation: 0,
        surfaceTintColor: Colors.transparent,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_rounded, color: AppTheme.textPrimary),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(l.supportFaqTitle,
          style: const TextStyle(
            color: AppTheme.textPrimary,
            fontWeight: FontWeight.w800,
            fontSize: 18,
          )),
      ),
      body: ListView.builder(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 40),
        itemCount: faq.length,
        itemBuilder: (ctx, i) {
          final cat = faq[i];
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (i > 0) const SizedBox(height: 16),
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: Text(
                  (cat['category'] as String).toUpperCase(),
                  style: const TextStyle(
                    fontSize: 10, fontWeight: FontWeight.w700,
                    color: AppTheme.textMuted, letterSpacing: 3,
                  ),
                ),
              ),
              ...(cat['items'] as List<Map<String, String>>).map((item) =>
                _FaqTile(question: item['q']!, answer: item['a']!),
              ),
            ],
          );
        },
      ),
    );
  }

  static List<Map<String, dynamic>> _faqData(String locale) {
    switch (locale) {
      case 'fa':
        return _faqFa;
      case 'ru':
        return _faqRu;
      default:
        return _faqEn;
    }
  }

  static final _faqRu = <Map<String, dynamic>>[
    {
      'category': 'Начало работы',
      'items': <Map<String, String>>[
        {'q': 'Как скачать SafeNet service?', 'a': 'Скачайте APK по ссылке https://safenetsystem.duckdns.org/download/app или через Telegram-бот @safevpn_middleeast. iOS версия в разработке.'},
        {'q': 'Нужна ли регистрация?', 'a': 'Нет. Приложение автоматически создаёт анонимный аккаунт при первом запуске. Никаких email или паролей.'},
        {'q': 'Как подключиться к service?', 'a': 'Нажмите большую кнопку CONNECT на главном экране. Подключение займёт 3-5 секунд.'},
      ],
    },
    {
      'category': 'Триал и Premium',
      'items': <Map<String, String>>[
        {'q': 'Что входит в бесплатный триал?', 'a': '3 дня полного безлимита — все серверы, все режимы обхода, без ограничений по времени сессии.'},
        {'q': 'Что будет после триала?', 'a': 'Сессии ограничены 5 минутами. Для безлимита оформите Premium подписку.'},
        {'q': 'Как оплатить Premium?', 'a': 'Перейдите на вкладку «Премиум», выберите план и оплатите через CryptoBot в USDT TRC20 или TON. Активация мгновенная.'},
        {'q': 'Можно ли вернуть деньги?', 'a': 'Да, в течение 24 часов после оплаты, если вы не использовали сервис. Напишите в поддержку.'},
      ],
    },
    {
      'category': 'Режимы обхода',
      'items': <Map<String, String>>[
        {'q': 'Какой режим выбрать?', 'a': '«Максимальный» — лучший вариант для большинства. Он комбинирует все технологии. Если не работает — попробуйте «Тунель» или «Супер».'},
        {'q': 'Что такое ByeDPI и AmneziaWG?', 'a': 'ByeDPI обходит DPI-блокировки провайдера. AmneziaWG — WireGuard-туннель с обфускацией. Вместе они обеспечивают максимальную проходимость.'},
      ],
    },
    {
      'category': 'Безопасность',
      'items': <Map<String, String>>[
        {'q': 'Безопасно ли использовать SafeNet?', 'a': 'Да. Мы используем шифрование военного класса (WireGuard + Reality). Ваш трафик не логируется.'},
        {'q': 'Что такое Kill Switch?', 'a': 'При обрыве service-соединения Kill Switch блокирует весь интернет-трафик, чтобы ваш реальный IP не утёк.'},
        {'q': 'Легально ли использовать service в ОАЭ?', 'a': 'service легален для законных целей. Использование service для доступа к законным сервисам не является нарушением.'},
      ],
    },
    {
      'category': 'Устройства и аккаунт',
      'items': <Map<String, String>>[
        {'q': 'Можно ли использовать на нескольких устройствах?', 'a': 'Каждое устройство получает свой UUID. Для нескольких устройств потребуются отдельные подписки.'},
        {'q': 'Как перенести аккаунт?', 'a': 'Скопируйте UUID из настроек и сообщите его в поддержку — мы привяжем подписку к новому устройству.'},
        {'q': 'Будет ли iOS версия?', 'a': 'Да, iOS версия SafeNet service находится в активной разработке.'},
      ],
    },
    {
      'category': 'Реферальная программа',
      'items': <Map<String, String>>[
        {'q': 'Как работает реферальная программа?', 'a': 'Приведите 1-10 друзей — получите 50% скидку. От 11 рефералов — станьте партнёром с выплатами в TON.'},
        {'q': 'Как пригласить друга?', 'a': 'На главном экране есть QR-код и реферальная ссылка. Поделитесь ими — друг автоматически привяжется к вашему коду.'},
      ],
    },
  ];

  static final _faqEn = <Map<String, dynamic>>[
    {
      'category': 'Getting Started',
      'items': <Map<String, String>>[
        {'q': 'How to download SafeNet service?', 'a': 'Download the APK from https://safenetsystem.duckdns.org/download/app or via Telegram bot @safevpn_middleeast. iOS version is coming soon.'},
        {'q': 'Is registration required?', 'a': 'No. The app automatically creates an anonymous account on first launch. No emails or passwords needed.'},
        {'q': 'How to connect to service?', 'a': 'Tap the large CONNECT button on the home screen. Connection takes 3-5 seconds.'},
      ],
    },
    {
      'category': 'Trial & Premium',
      'items': <Map<String, String>>[
        {'q': 'What does the free trial include?', 'a': '3 days of full unlimited access — all servers, all bypass modes, no session time limits.'},
        {'q': 'What happens after the trial?', 'a': 'Sessions are limited to 5 minutes. Get a Premium subscription for unlimited access.'},
        {'q': 'How to pay for Premium?', 'a': 'Go to the Premium tab, choose a plan and pay via CryptoBot in USDT TRC20 or TON. Activation is instant.'},
        {'q': 'Can I get a refund?', 'a': 'Yes, within 24 hours of payment if you haven\'t used the service. Contact support.'},
      ],
    },
    {
      'category': 'Bypass Modes',
      'items': <Map<String, String>>[
        {'q': 'Which mode should I choose?', 'a': '"Maximum" is best for most users — it combines all technologies. If it doesn\'t work, try "Tunnel" or "Super".'},
        {'q': 'What are ByeDPI and AmneziaWG?', 'a': 'ByeDPI bypasses ISP DPI blocks. AmneziaWG is a WireGuard tunnel with obfuscation. Together they provide maximum connectivity.'},
      ],
    },
    {
      'category': 'Security',
      'items': <Map<String, String>>[
        {'q': 'Is SafeNet safe to use?', 'a': 'Yes. We use military-grade encryption (WireGuard + Reality). Your traffic is not logged.'},
        {'q': 'What is Kill Switch?', 'a': 'If the service connection drops, Kill Switch blocks all internet traffic to prevent your real IP from leaking.'},
        {'q': 'Is service legal in UAE?', 'a': 'service is legal for lawful purposes. Using service to access legitimate services is not a violation.'},
      ],
    },
    {
      'category': 'Devices & Account',
      'items': <Map<String, String>>[
        {'q': 'Can I use on multiple devices?', 'a': 'Each device gets its own UUID. Separate subscriptions are needed for multiple devices.'},
        {'q': 'How to transfer my account?', 'a': 'Copy your UUID from settings and share it with support — we\'ll link your subscription to the new device.'},
        {'q': 'Will there be an iOS version?', 'a': 'Yes, the iOS version of SafeNet service is in active development.'},
      ],
    },
    {
      'category': 'Referral Program',
      'items': <Map<String, String>>[
        {'q': 'How does the referral program work?', 'a': 'Bring 1-10 friends — get 50% discount. From 11 referrals — become a partner with TON payouts.'},
        {'q': 'How to invite a friend?', 'a': 'On the home screen there\'s a QR code and referral link. Share them — your friend will be automatically linked to your code.'},
      ],
    },
  ];

  static final _faqFa = <Map<String, dynamic>>[
    {
      'category': 'شروع کار',
      'items': <Map<String, String>>[
        {'q': 'چگونه SafeNet service را دانلود کنم؟', 'a': 'فایل APK را از https://safenetsystem.duckdns.org/download/app یا ربات تلگرام @safevpn_middleeast دانلود کنید. نسخه iOS به زودی.'},
        {'q': 'آیا ثبت‌نام لازم است؟', 'a': 'خیر. برنامه به‌طور خودکار یک حساب ناشناس ایجاد می‌کند. بدون ایمیل یا رمز عبور.'},
        {'q': 'چگونه به service متصل شوم؟', 'a': 'دکمه بزرگ CONNECT را در صفحه اصلی بزنید. اتصال ۳ تا ۵ ثانیه طول می‌کشد.'},
      ],
    },
    {
      'category': 'آزمایشی و پریمیوم',
      'items': <Map<String, String>>[
        {'q': 'دوره آزمایشی رایگان شامل چه می‌شود؟', 'a': '۳ روز دسترسی نامحدود — همه سرورها، همه حالت‌ها، بدون محدودیت زمانی.'},
        {'q': 'بعد از دوره آزمایشی چه می‌شود؟', 'a': 'جلسات به ۵ دقیقه محدود می‌شود. برای دسترسی نامحدود پریمیوم تهیه کنید.'},
        {'q': 'چگونه پریمیوم بخرم؟', 'a': 'به تب پریمیوم بروید، طرح را انتخاب و از طریق CryptoBot با USDT یا TON پرداخت کنید. فعال‌سازی فوری.'},
        {'q': 'آیا بازپرداخت ممکن است؟', 'a': 'بله، ظرف ۲۴ ساعت پس از پرداخت اگر از سرویس استفاده نکرده باشید. با پشتیبانی تماس بگیرید.'},
      ],
    },
    {
      'category': 'حالت‌های دور زدن',
      'items': <Map<String, String>>[
        {'q': 'کدام حالت را انتخاب کنم؟', 'a': '«حداکثر» بهترین گزینه برای اکثر کاربران است. اگر کار نکرد، «تونل» یا «سوپر» را امتحان کنید.'},
        {'q': 'ByeDPI و AmneziaWG چیست؟', 'a': 'ByeDPI فیلترینگ DPI را دور می‌زند. AmneziaWG یک تونل WireGuard با مبهم‌سازی است.'},
      ],
    },
    {
      'category': 'امنیت',
      'items': <Map<String, String>>[
        {'q': 'آیا استفاده از SafeNet امن است؟', 'a': 'بله. ما از رمزنگاری نظامی (WireGuard + Reality) استفاده می‌کنیم. ترافیک شما ثبت نمی‌شود.'},
        {'q': 'Kill Switch چیست؟', 'a': 'اگر اتصال service قطع شود، Kill Switch تمام ترافیک اینترنت را مسدود می‌کند تا IP واقعی شما فاش نشود.'},
        {'q': 'آیا service در امارات قانونی است؟', 'a': 'service برای اهداف قانونی مجاز است. استفاده از service برای دسترسی به خدمات قانونی تخلف نیست.'},
      ],
    },
    {
      'category': 'دستگاه‌ها و حساب',
      'items': <Map<String, String>>[
        {'q': 'آیا روی چند دستگاه قابل استفاده است؟', 'a': 'هر دستگاه UUID خاص خود را دارد. برای چند دستگاه به اشتراک‌های جداگانه نیاز است.'},
        {'q': 'چگونه حساب خود را منتقل کنم؟', 'a': 'UUID خود را از تنظیمات کپی کنید و به پشتیبانی بدهید — ما اشتراک را به دستگاه جدید منتقل می‌کنیم.'},
        {'q': 'آیا نسخه iOS خواهد آمد؟', 'a': 'بله، نسخه iOS در حال توسعه فعال است.'},
      ],
    },
    {
      'category': 'برنامه معرفی',
      'items': <Map<String, String>>[
        {'q': 'برنامه معرفی چگونه کار می‌کند؟', 'a': '۱ تا ۱۰ دوست بیاورید — ۵۰٪ تخفیف بگیرید. از ۱۱ زیرمجموعه — شریک با درآمد TON شوید.'},
        {'q': 'چگونه دوست دعوت کنم؟', 'a': 'در صفحه اصلی کد QR و لینک معرفی هست. آن‌ها را به اشتراک بگذارید.'},
      ],
    },
  ];
}

class _FaqTile extends StatefulWidget {
  final String question;
  final String answer;
  const _FaqTile({required this.question, required this.answer});

  @override
  State<_FaqTile> createState() => _FaqTileState();
}

class _FaqTileState extends State<_FaqTile> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: GestureDetector(
        onTap: () => setState(() => _expanded = !_expanded),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppTheme.surface,
            border: Border.all(
              color: _expanded ? AppTheme.primary.withValues(alpha: 0.3) : AppTheme.border,
            ),
            borderRadius: BorderRadius.circular(16),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(widget.question,
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        color: _expanded ? AppTheme.primary : AppTheme.textPrimary,
                      )),
                  ),
                  Icon(
                    _expanded ? Icons.expand_less_rounded : Icons.expand_more_rounded,
                    color: AppTheme.textMuted, size: 20,
                  ),
                ],
              ),
              if (_expanded) ...[
                const SizedBox(height: 10),
                Text(widget.answer,
                  style: const TextStyle(
                    fontSize: 12, color: AppTheme.textSecondary, height: 1.5,
                  )),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
