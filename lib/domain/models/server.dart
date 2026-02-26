class VpnServer {
  final String id;
  final String name;
  final String country;
  final String? city;
  final String serverType; // amneziawg | byedpi
  final double load;
  final int? latencyMs;
  final bool isActive;

  const VpnServer({
    required this.id,
    required this.name,
    required this.country,
    this.city,
    required this.serverType,
    required this.load,
    this.latencyMs,
    required this.isActive,
  });

  factory VpnServer.fromJson(Map<String, dynamic> j) => VpnServer(
    id:         j['id'],
    name:       j['name'],
    country:    j['country'],
    city:       j['city'],
    serverType: j['server_type'] ?? 'amneziawg',
    load:       (j['current_load'] ?? 0).toDouble(),
    latencyMs:  j['latency_ms'],
    isActive:   j['is_active'] ?? true,
  );

  String get flag => {
    'TR': '🇹🇷', 'EG': '🇪🇬', 'PK': '🇵🇰',
    'ID': '🇮🇩', 'AE': '🇦🇪', 'VE': '🇻🇪', 'SA': '🇸🇦',
  }[country] ?? '🌍';

  /// Флаги аудитории — кому предназначен профиль
  String get audienceFlags => const {
    'TR': '🇮🇷',  // пока работаем на Иран
    'AE': '🇦🇪',
    'EG': '🇪🇬',
    'SA': '🇸🇦',
    'PK': '🇵🇰',
    'ID': '🇮🇩',
    'VE': '🇻🇪',
  }[country] ?? flag;

  /// Название аудитории (человекочитаемое)
  String get audienceName => const {
    'TR': 'Иран',
    'AE': 'ОАЭ',
    'EG': 'Египет',
    'SA': 'Саудовская Аравия',
    'PK': 'Пакистан',
    'ID': 'Индонезия',
    'VE': 'Венесуэла',
  }[country] ?? country;

  /// Метка «для» — показывает целевую аудиторию, не расположение сервера
  String get forLabel => 'для $audienceFlags $audienceName';

  String get loadLabel {
    if (load < 30) return 'Low';
    if (load < 70) return 'Medium';
    return 'High';
  }

  /// Совместимость с UI: пинг в мс
  int get ping => latencyMs ?? 0;

  /// Совместимость с UI: режим VPN
  String get mode => serverType;

  /// Совместимость с UI: город (fallback на страну)
  String get cityLabel => city ?? country;

  static const defaults = [
    VpnServer(
      id: '3', name: 'AE-1', country: 'AE',
      city: 'Dubai', serverType: 'AmneziaWG',
      load: 35, latencyMs: 31, isActive: true,
    ),
    VpnServer(
      id: '1', name: 'TR-1', country: 'TR',
      city: 'Istanbul', serverType: 'ByeDPI',
      load: 42, latencyMs: 24, isActive: true,
    ),
    VpnServer(
      id: '2', name: 'EG-1', country: 'EG',
      city: 'Cairo', serverType: 'AmneziaWG',
      load: 61, latencyMs: 38, isActive: true,
    ),
  ];
}
