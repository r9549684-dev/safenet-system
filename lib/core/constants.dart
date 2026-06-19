class AppConstants {
  // API
  // All-in-One MVP VPS (38.180.253.219)
  static const String apiBaseUrl = 'http://38.180.253.219:8000';
  static const Duration connectTimeout = Duration(seconds: 12);
  static const Duration receiveTimeout = Duration(seconds: 15);

  // Trial
  static const int trialDays = 3;
  static const int freeDisconnectMinutes = 5;

  // Storage keys
  static const String keyAccessToken = 'access_token';
  static const String keyDeviceId   = 'device_id';
  static const String keyLanguage   = 'language';
  static const String keyCountry    = 'country';
  static const String keyOnboarded  = 'onboarded';

  // Countries
  static const Map<String, Map<String, String>> countries = {
    'TR': {'name': 'Turkey',    'flag': '🇹🇷', 'lang': 'tr'},
    'EG': {'name': 'Egypt',     'flag': '🇪🇬', 'lang': 'ar'},
    'PK': {'name': 'Pakistan',  'flag': '🇵🇰', 'lang': 'ur'},
    'ID': {'name': 'Indonesia', 'flag': '🇮🇩', 'lang': 'id'},
    'AE': {'name': 'UAE',       'flag': '🇦🇪', 'lang': 'ar'},
    'VE': {'name': 'Venezuela', 'flag': '🇻🇪', 'lang': 'es'},
  };

  // Pricing (USD) — fallback, актуальные цены fetchются через /subscriptions/pricing?country=
  // TR: monthly $4.99,  AE: monthly $9.99  (коэффициент от глобального $5.99)
  static const Map<String, Map<String, double>> pricing = {
    'TR': {'weekly': 2.49, 'monthly': 4.99, 'quarterly': 12.49, 'yearly': 24.99},
    'AE': {'weekly': 4.99, 'monthly': 9.99, 'quarterly': 24.99, 'yearly': 49.99},
    'EG': {'monthly': 1.99, 'yearly': 19.99},
    'PK': {'monthly': 1.49, 'yearly': 14.99},
    'ID': {'monthly': 1.99, 'yearly': 19.99},
    'VE': {'monthly': 1.99, 'yearly': 19.99},
  };

  // service Channel
  static const String vpnMethodChannel = 'com.safenet.vpn/methods';
}
