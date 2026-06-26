import 'dart:convert';

/// Конвертирует raw Trojan конфиг (из бэкенд) в singbox JSON-строку.
///
/// sing-box формат для Trojan:
///   { "outbounds": [ { "type": "trojan", "server": "...", "server_port": ..., "password": "...", "tls": {...} } ] }
class TrojanSingboxConverter {
  static String toSingboxJson(Map<String, dynamic> trojanConfig) {
    final address = _require(trojanConfig, 'address');
    final port = _requireInt(trojanConfig, 'port');
    final password = _require(trojanConfig, 'password');
    final sni = (trojanConfig['sni'] as String?) ?? 'www.microsoft.com';
    final insecure = trojanConfig['insecure'] as bool? ?? true;

    final outbound = <String, dynamic>{
      'type': 'trojan',
      'tag': 'proxy',
      'server': address,
      'server_port': port,
      'password': password,
      'tls': <String, dynamic>{
        'enabled': true,
        'server_name': sni,
        'insecure': insecure,
      },
    };

    return jsonEncode(<String, dynamic>{
      'outbounds': <dynamic>[outbound],
    });
  }

  static bool isValid(Map<String, dynamic> trojanConfig) {
    final password = trojanConfig['password'];
    if (password == null || (password as String).isEmpty) return false;
    final address = trojanConfig['address'];
    if (address == null || (address as String).isEmpty) return false;
    final port = trojanConfig['port'];
    if (port == null) return false;
    return true;
  }

  static String _require(Map map, String key) {
    final v = map[key];
    if (v == null || (v is String && v.isEmpty)) {
      throw FormatException('trojan_config: отсутствует обязательное поле "$key"');
    }
    return v.toString();
  }

  static int _requireInt(Map map, String key) {
    final v = map[key];
    if (v == null) {
      throw FormatException('trojan_config: отсутствует обязательное поле "$key"');
    }
    if (v is int) return v;
    return int.tryParse(v.toString()) ??
        (throw FormatException('trojan_config: "$key" не является int'));
  }
}
