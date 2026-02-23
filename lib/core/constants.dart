class AppConstants {
  // API
  static const String apiBaseUrl = 'http://89.208.107.67:8500';
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

  // Pricing (USD)
  static const Map<String, Map<String, double>> pricing = {
    'TR': {'monthly': 2.99, 'yearly': 29.99, 'lifetime': 59.99},
    'EG': {'monthly': 1.99, 'yearly': 19.99, 'lifetime': 39.99},
    'PK': {'monthly': 1.49, 'yearly': 14.99, 'lifetime': 29.99},
    'ID': {'monthly': 1.99, 'yearly': 19.99, 'lifetime': 39.99},
    'AE': {'monthly': 4.99, 'yearly': 49.99, 'lifetime': 99.99},
    'VE': {'monthly': 1.99, 'yearly': 19.99, 'lifetime': 39.99},
  };

  // VPN Channel (com.safenet.vpn/methods — по документу)
  static const String vpnMethodChannel = 'com.safenet.vpn/methods';
}
