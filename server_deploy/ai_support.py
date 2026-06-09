"""
AI Support — встроенный FAQ-агент для SafeNet service.
TopicFilter + keyword search по FAQ-базе, без тяжёлых зависимостей.
"""
import re
from typing import Optional, List, Tuple, Dict

# ── service темы (ключевые слова) ───────────────────────────────────────────
VPN_TOPICS: Dict[str, List[str]] = {
    "connection": [
        "подключ", "connect", "اتصال", "bağlan",
        "ошибка", "error", "خطا", "hata",
        "сервер", "server", "سرور", "sunucu",
        "ип", "ip", "айпи", "آی پی",
        "timeout", "таймаут",
    ],
    "payment": [
        "оплат", "pay", "payment", "پرداخت", "öde",
        "тариф", "tariff", "تعرفه", "tarife",
        "подписк", "subscription", "اشتراک", "abonelik",
        "звезд", "star", "ton", "usdt", "крипт", "crypto",
        "premium", "премиум", "پریمیوم",
        "цена", "price", "стоимост", "cost",
    ],
    "technical": [
        "настройк", "setting", "تنظیمات", "ayar",
        "протокол", "protocol", "پروتکل",
        "amnezia", "wireguard", "vless", "byedpi",
        "скорость", "speed", "سرعت", "hız",
        "service", "сервис", "فیلترشکن",
        "режим", "mode", "حالت",
        "максимальн", "maximum", "tunnel", "тунел", "super", "супер",
    ],
    "account": [
        "аккаунт", "account", "حساب", "hesap",
        "логин", "login", "ورود",
        "uuid", "device", "устройств", "دستگاه",
        "перенес", "transfer", "منتقل",
    ],
    "support": [
        "помощ", "help", "کمک", "yardım",
        "проблем", "problem", "مشکل", "sorun",
        "не работ", "not work", "کار نمی",
        "поддержк", "support", "پشتیبان",
    ],
    "security": [
        "безопасн", "safe", "secure", "امن",
        "шифрован", "encrypt", "رمزنگاری",
        "kill switch", "логирован", "log", "privacy",
        "легальн", "legal", "قانون",
    ],
    "referral": [
        "рефер", "referral", "invite", "пригласи", "دعوت",
        "партнёр", "partner", "affiliate", "شریک",
        "реферальн", "معرفی",
    ],
    "trial": [
        "триал", "trial", "آزمایش",
        "бесплатн", "free", "رایگان",
        "пробн", "тест", "test",
    ],
}

# ── Off-topic паттерны ──────────────────────────────────────────────────
OFF_TOPIC_PATTERNS = [
    r"\b(политик|политика|политическ)\b",
    r"\b(войн|война|военн)\b",
    r"\b(религи|религия|религиозн)\b",
    r"\b(секс|порно|эрот)\b",
    r"\b(наркот|наркоти|drug)\b",
    r"\b(казино|gambl|bet|ставк)\b",
    r"\b(взлом|hack|exploit)\b",
    r"\b(спам|spam|рассылк)\b",
]
_compiled_off_topic = [re.compile(p, re.IGNORECASE) for p in OFF_TOPIC_PATTERNS]


# ── FAQ база (ru / en / fa) ────────────────────────────────────────────
FAQ_DB: Dict[str, List[Dict[str, str]]] = {
    "ru": [
        {"q": "Как скачать SafeNet service?", "a": "Скачайте APK с нашего сайта safenetvpn.com или через Telegram-бот @SafeBypass_bot → /download. iOS версия в разработке.", "t": "connection"},
        {"q": "Нужна ли регистрация?", "a": "Нет. Приложение автоматически создаёт анонимный аккаунт при первом запуске. Никаких email или паролей.", "t": "account"},
        {"q": "Как подключиться к service?", "a": "Нажмите большую кнопку CONNECT на главном экране. Подключение займёт 3-5 секунд.", "t": "connection"},
        {"q": "Что входит в бесплатный триал?", "a": "3 дня полного безлимита — все серверы, все режимы обхода, без ограничений по времени сессии.", "t": "trial"},
        {"q": "Что будет после триала?", "a": "Сессии ограничены 5 минутами. Для безлимита оформите Premium подписку.", "t": "trial"},
        {"q": "Как оплатить Premium?", "a": "Перейдите на вкладку «Премиум» в приложении, выберите план и оплатите через CryptoBot в USDT TRC20 или TON. Активация мгновенная.", "t": "payment"},
        {"q": "Сколько стоит подписка?", "a": "Неделя — $2.99, месяц — $5.99, 3 месяца — $14.99, год — $29.99. Для ОАЭ/Ближнего Востока: неделя — $4.99, месяц — $9.99, 3 мес — $24.99, год — $49.99.", "t": "payment"},
        {"q": "Можно ли вернуть деньги?", "a": "Криптоплатежи, как правило, невозвратные. Если сервис не работает после устранения неполадок — напишите в поддержку, обсудим варианты.", "t": "payment"},
        {"q": "Какой режим выбрать?", "a": "«Максимальный» — лучший вариант для большинства. Он комбинирует AmneziaWG + ByeDPI. Если не работает — попробуйте «Тунель» или «Супер».", "t": "technical"},
        {"q": "Что такое ByeDPI и AmneziaWG?", "a": "ByeDPI обходит DPI-блокировки провайдера. AmneziaWG — WireGuard-туннель с обфускацией. Вместе они обеспечивают максимальную проходимость.", "t": "technical"},
        {"q": "service медленно работает", "a": "1) Проверьте план: триал — до 3 Мбит/с, Premium — до 10 Мбит/с. 2) Попробуйте другой сервер. 3) Смените режим (Максимальный → Тунель). 4) Перезапустите приложение.", "t": "technical"},
        {"q": "Ошибка подключения / таймаут", "a": "1) Попробуйте другой сервер. 2) Смените режим: Максимальный → Тунель → Супер. 3) Проверьте, не истёк ли триал. 4) Обновите приложение через /download.", "t": "connection"},
        {"q": "Безопасно ли использовать SafeNet?", "a": "Да. Мы используем шифрование военного класса — WireGuard (ChaCha20-Poly1305) + Reality (TLS 1.3). Ваш трафик не логируется.", "t": "security"},
        {"q": "Что такое Kill Switch?", "a": "При обрыве service-соединения Kill Switch блокирует весь интернет-трафик, чтобы ваш реальный IP не утёк.", "t": "security"},
        {"q": "Легально ли service в ОАЭ?", "a": "service легален для законных целей — доступ к сервисам, VoIP звонки, удалённая работа. Использование для незаконных действий запрещено.", "t": "security"},
        {"q": "Можно ли использовать на нескольких устройствах?", "a": "Каждое устройство получает свой UUID. Для нескольких устройств потребуются отдельные подписки.", "t": "account"},
        {"q": "Как перенести аккаунт?", "a": "Скопируйте UUID из настроек и сообщите его в поддержку — мы привяжем подписку к новому устройству.", "t": "account"},
        {"q": "Как работает реферальная программа?", "a": "Приведите 1-10 друзей — получите 50% скидку. От 11 рефералов — станьте партнёром с CPA $1.5 в TON за каждую оплату друга.", "t": "referral"},
        {"q": "WhatsApp/FaceTime не работает через service", "a": "VoIP блокируется в ОАЭ. Выберите сервер UAE, режим «Максимальный» (AmneziaWG + ByeDPI), перезапустите подключение.", "t": "connection"},
        {"q": "Будет ли iOS версия?", "a": "Да, iOS версия SafeNet service находится в активной разработке.", "t": "connection"},
        {"q": "Как продлить подписку?", "a": "SafeService НЕ автопродлевает подписку. Для продления отправьте /pay в @SafeBypass_bot. Новый период добавляется к оставшемуся.", "t": "payment"},
    ],
    "en": [
        {"q": "How to download SafeNet service?", "a": "Download the APK from safenetvpn.com or via Telegram bot @SafeBypass_bot → /download. iOS version is coming soon.", "t": "connection"},
        {"q": "Is registration required?", "a": "No. The app automatically creates an anonymous account on first launch. No emails or passwords needed.", "t": "account"},
        {"q": "How to connect to service?", "a": "Tap the large CONNECT button on the home screen. Connection takes 3-5 seconds.", "t": "connection"},
        {"q": "What does the free trial include?", "a": "3 days of full unlimited access — all servers, all bypass modes, no session time limits.", "t": "trial"},
        {"q": "What happens after the trial?", "a": "Sessions are limited to 5 minutes. Get a Premium subscription for unlimited access.", "t": "trial"},
        {"q": "How to pay for Premium?", "a": "Go to the Premium tab in the app, choose a plan and pay via CryptoBot in USDT TRC20 or TON. Activation is instant.", "t": "payment"},
        {"q": "How much does the subscription cost?", "a": "Weekly — $2.99, Monthly — $5.99, Quarterly — $14.99, Yearly — $29.99. UAE/Middle East: Weekly — $4.99, Monthly — $9.99, Quarterly — $24.99, Yearly — $49.99.", "t": "payment"},
        {"q": "Can I get a refund?", "a": "Crypto payments are generally non-refundable. If the service is not working after troubleshooting, contact support to discuss options.", "t": "payment"},
        {"q": "Which mode should I choose?", "a": "\"Maximum\" is best for most users — it combines AmneziaWG + ByeDPI. If it doesn't work, try \"Tunnel\" or \"Super\".", "t": "technical"},
        {"q": "What are ByeDPI and AmneziaWG?", "a": "ByeDPI bypasses ISP DPI blocks. AmneziaWG is a WireGuard tunnel with obfuscation. Together they provide maximum connectivity.", "t": "technical"},
        {"q": "service is slow", "a": "1) Check your plan: trial — up to 3 Mbps, Premium — up to 10 Mbps. 2) Try a different server. 3) Switch mode (Maximum → Tunnel). 4) Restart the app.", "t": "technical"},
        {"q": "Connection error / timeout", "a": "1) Try a different server. 2) Switch mode: Maximum → Tunnel → Super. 3) Check if trial expired. 4) Update the app via /download.", "t": "connection"},
        {"q": "Is SafeNet safe to use?", "a": "Yes. We use military-grade encryption — WireGuard (ChaCha20-Poly1305) + Reality (TLS 1.3). Your traffic is not logged.", "t": "security"},
        {"q": "What is Kill Switch?", "a": "If the service connection drops, Kill Switch blocks all internet traffic to prevent your real IP from leaking.", "t": "security"},
        {"q": "Is service legal in UAE?", "a": "service is legal for lawful purposes — accessing services, VoIP calls, remote work. Using service for illegal activities is prohibited.", "t": "security"},
        {"q": "Can I use on multiple devices?", "a": "Each device gets its own UUID. Separate subscriptions are needed for multiple devices.", "t": "account"},
        {"q": "How to transfer my account?", "a": "Copy your UUID from settings and share it with support — we'll link your subscription to the new device.", "t": "account"},
        {"q": "How does the referral program work?", "a": "Bring 1-10 friends — get 50% discount. From 11 referrals — become a partner with CPA $1.5 in TON per friend's payment.", "t": "referral"},
        {"q": "WhatsApp/FaceTime calls don't work", "a": "VoIP is blocked in UAE. Select UAE server, use Maximum mode (AmneziaWG + ByeDPI), restart connection.", "t": "connection"},
        {"q": "Will there be an iOS version?", "a": "Yes, the iOS version of SafeNet service is in active development.", "t": "connection"},
        {"q": "How to renew subscription?", "a": "SafeService does NOT auto-renew. To renew, send /pay to @SafeBypass_bot. The new period adds to your remaining time.", "t": "payment"},
    ],
    "fa": [
        {"q": "چگونه SafeNet service را دانلود کنم؟", "a": "فایل APK را از safenetvpn.com یا ربات تلگرام @SafeBypass_bot → /download دانلود کنید. نسخه iOS به زودی.", "t": "connection"},
        {"q": "آیا ثبت‌نام لازم است؟", "a": "خیر. برنامه به‌طور خودکار یک حساب ناشناس ایجاد می‌کند. بدون ایمیل یا رمز عبور.", "t": "account"},
        {"q": "چگونه به service متصل شوم؟", "a": "دکمه بزرگ CONNECT را در صفحه اصلی بزنید. اتصال ۳ تا ۵ ثانیه طول می‌کشد.", "t": "connection"},
        {"q": "دوره آزمایشی رایگان شامل چه می‌شود؟", "a": "۳ روز دسترسی نامحدود — همه سرورها، همه حالت‌ها، بدون محدودیت زمانی.", "t": "trial"},
        {"q": "بعد از دوره آزمایشی چه می‌شود؟", "a": "جلسات به ۵ دقیقه محدود می‌شود. برای دسترسی نامحدود پریمیوم تهیه کنید.", "t": "trial"},
        {"q": "چگونه پریمیوم بخرم؟", "a": "به تب پریمیوم بروید، طرح را انتخاب و از طریق CryptoBot با USDT یا TON پرداخت کنید. فعال‌سازی فوری.", "t": "payment"},
        {"q": "قیمت اشتراک چقدر است؟", "a": "هفتگی — ۲.۹۹$، ماهانه — ۵.۹۹$، سه‌ماهه — ۱۴.۹۹$، سالانه — ۲۹.۹۹$. منطقه خلیج: هفتگی — ۴.۹۹$، ماهانه — ۹.۹۹$.", "t": "payment"},
        {"q": "کدام حالت را انتخاب کنم؟", "a": "«حداکثر» بهترین گزینه برای اکثر کاربران است — ترکیب AmneziaWG + ByeDPI. اگر کار نکرد، «تونل» یا «سوپر» را امتحان کنید.", "t": "technical"},
        {"q": "ByeDPI و AmneziaWG چیست؟", "a": "ByeDPI فیلترینگ DPI را دور می‌زند. AmneziaWG یک تونل WireGuard با مبهم‌سازی است. با هم حداکثر اتصال را فراهم می‌کنند.", "t": "technical"},
        {"q": "آیا استفاده از SafeNet امن است؟", "a": "بله. ما از رمزنگاری نظامی — WireGuard (ChaCha20-Poly1305) + Reality (TLS 1.3) استفاده می‌کنیم. ترافیک شما ثبت نمی‌شود.", "t": "security"},
        {"q": "Kill Switch چیست؟", "a": "اگر اتصال service قطع شود، Kill Switch تمام ترافیک اینترنت را مسدود می‌کند تا IP واقعی شما فاش نشود.", "t": "security"},
        {"q": "آیا روی چند دستگاه قابل استفاده است؟", "a": "هر دستگاه UUID خاص خود را دارد. برای چند دستگاه به اشتراک‌های جداگانه نیاز است.", "t": "account"},
        {"q": "چگونه حساب خود را منتقل کنم؟", "a": "UUID خود را از تنظیمات کپی کنید و به پشتیبانی بدهید — ما اشتراک را به دستگاه جدید منتقل می‌کنیم.", "t": "account"},
        {"q": "برنامه معرفی چگونه کار می‌کند؟", "a": "۱ تا ۱۰ دوست بیاورید — ۵۰٪ تخفیف بگیرید. از ۱۱ زیرمجموعه — شریک با درآمد TON شوید.", "t": "referral"},
        {"q": "service کند است", "a": "۱) طرح خود را بررسی کنید: آزمایشی — تا ۳ مگابیت، پریمیوم — تا ۱۰ مگابیت. ۲) سرور دیگری امتحان کنید. ۳) حالت را عوض کنید. ۴) برنامه را ریستارت کنید.", "t": "technical"},
        {"q": "خطای اتصال / تایم‌اوت", "a": "۱) سرور دیگری امتحان کنید. ۲) حالت را عوض کنید: حداکثر → تونل → سوپر. ۳) بررسی کنید دوره آزمایشی تمام نشده باشد. ۴) برنامه را آپدیت کنید.", "t": "connection"},
    ],
}


# ── Приветствия ─────────────────────────────────────────────────────────
GREETINGS = {
    "ru": "👋 Привет! Я SEIFY — AI-помощник SafeNet service.\n\nЯ могу помочь с:\n• Подключением и настройкой service\n• Оплатой и подписками\n• Выбором режима обхода\n• Технической поддержкой\n\nЗадайте ваш вопрос!",
    "en": "👋 Hi! I'm SEIFY — SafeNet service AI assistant.\n\nI can help with:\n• service connection and setup\n• Payment and subscriptions\n• Choosing bypass mode\n• Technical support\n\nAsk me anything!",
    "fa": "👋 سلام! من SEIFY هستم — دستیار هوش مصنوعی SafeNet service.\n\nمی‌توانم کمک کنم با:\n• اتصال و تنظیم service\n• پرداخت و اشتراک\n• انتخاب حالت دور زدن\n• پشتیبانی فنی\n\nسوال خود را بپرسید!",
}

OFF_TOPIC_RESPONSES = {
    "ru": "⚠️ Я могу отвечать только на вопросы о SafeNet service.\n\nСпросите о:\n• Подключении к серверам\n• Оплате и тарифах\n• Настройке service\n• Проблемах с подключением",
    "en": "⚠️ I can only answer questions about SafeNet service.\n\nPlease ask about:\n• Connecting to servers\n• Payment and tariffs\n• service setup\n• Connection issues",
    "fa": "⚠️ من فقط می‌توانم به سوالات مربوط به SafeNet service پاسخ دهم.\n\nلطفاً بپرسید درباره:\n• اتصال به سرورها\n• پرداخت و تعرفه‌ها\n• تنظیم service\n• مشکلات اتصال",
}

FALLBACK_RESPONSES = {
    "ru": "🤔 К сожалению, я не нашёл точного ответа на ваш вопрос.\n\nПопробуйте:\n• Переформулировать вопрос\n• Посмотреть раздел FAQ в приложении\n• Написать оператору через Telegram: @SafeBypass_bot",
    "en": "🤔 Sorry, I couldn't find an exact answer to your question.\n\nTry:\n• Rephrasing your question\n• Checking the FAQ section in the app\n• Contacting an operator via Telegram: @SafeBypass_bot",
    "fa": "🤔 متأسفانه پاسخ دقیقی برای سوال شما پیدا نکردم.\n\nامتحان کنید:\n• سوال را دوباره بنویسید\n• بخش FAQ در برنامه را ببینید\n• با اپراتور از طریق تلگرام تماس بگیرید: @SafeBypass_bot",
}


# ── Функции ─────────────────────────────────────────────────────────────

def _is_greeting(text: str) -> bool:
    greetings = {"привет", "здравствуй", "hi", "hello", "hey", "سلام", "درود", "merhaba"}
    words = set(text.lower().split())
    return bool(words & greetings) and len(words) <= 4


def check_topic(text: str) -> Tuple[bool, Optional[str]]:
    """(is_vpn_topic, topic_name | 'off_topic' | None)"""
    text_lower = text.lower()
    for pattern in _compiled_off_topic:
        if pattern.search(text_lower):
            return (False, "off_topic")
    for topic_name, keywords in VPN_TOPICS.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                return (True, topic_name)
    general = ["service", "сервис", "интернет", "internet", "сеть", "network", "safenet", "SafeService"]
    for w in general:
        if w in text_lower:
            return (True, "general_vpn")
    return (False, None)


def search_faq(question: str, lang: str, top_k: int = 3) -> List[Dict[str, str]]:
    """Keyword-overlap поиск по встроенной FAQ-базе."""
    effective_lang = lang if lang in FAQ_DB else "en"
    faq_items = FAQ_DB[effective_lang]
    q_words = set(question.lower().split())
    scored = []
    for item in faq_items:
        item_words = set(item["q"].lower().split()) | set(item["a"].lower().split())
        overlap = len(q_words & item_words)
        if overlap >= 1:
            score = overlap / max(len(q_words), 1)
            scored.append((score, item))
    scored.sort(key=lambda x: -x[0])
    return [s[1] for s in scored[:top_k]]


def get_answer(message: str, lang: str = "en") -> dict:
    """
    Главная функция: принимает сообщение, возвращает ответ.
    Returns: {"answer": str, "source": str, "topic": str|None}
    """
    lang = lang if lang in ("ru", "en", "fa") else "en"

    # 1) Приветствие
    if _is_greeting(message):
        return {"answer": GREETINGS.get(lang, GREETINGS["en"]), "source": "greeting", "topic": None}

    # 2) Проверка темы
    is_vpn, topic = check_topic(message)
    if not is_vpn:
        if topic == "off_topic":
            return {"answer": OFF_TOPIC_RESPONSES.get(lang, OFF_TOPIC_RESPONSES["en"]), "source": "off_topic", "topic": "off_topic"}
        # Не распознана тема — всё равно ищем в FAQ
        results = search_faq(message, lang, top_k=2)
        if results and len(message.split()) >= 2:
            best = results[0]
            return {"answer": best["a"], "source": "faq", "topic": best.get("t")}
        return {"answer": FALLBACK_RESPONSES.get(lang, FALLBACK_RESPONSES["en"]), "source": "fallback", "topic": None}

    # 3) Поиск в FAQ
    results = search_faq(message, lang, top_k=3)
    if results:
        best = results[0]
        return {"answer": best["a"], "source": "faq", "topic": topic}

    # 4) Fallback
    return {"answer": FALLBACK_RESPONSES.get(lang, FALLBACK_RESPONSES["en"]), "source": "fallback", "topic": topic}
