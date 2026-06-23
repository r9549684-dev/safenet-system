import 'dart:convert';

/// Конвертирует raw VLESS+Reality конфиг (из бэкенд VpnConfigItem.vless_config)
/// в singbox JSON-строку (outbounds-only), готовую передать в SingboxVpn.start().
///
/// SingboxVpn (Android Kotlin) дополняет outbounds до full-конфига
/// через buildSingboxConfig(): mixed inbound, DNS, route private→direct.
class VlessSingboxConverter {
  /// Преобразует raw map (из backend) в singbox JSON-строку.
  ///
  /// [vlessConfig] — dict из бэкенда:
  ///   { "address", "port", "uuid", "flow", "security", "reality_opts": {...} }
  ///
  /// Возвращает JSON-строку вида:
  ///   { "outbounds": [ { "type": "vless", "flow": "xtls-rprx-vision", ... } ] }
  ///
  /// НЕ добавляет `transport.type=tcp` — sing-box 1.12+ FATAL на это для vision flow.
  static String toSingboxJson(Map<String, dynamic> vlessConfig) {
    final address = _require(vlessConfig, 'address');
    final port = _requireInt(vlessConfig, 'port');
    final uuid = _require(vlessConfig, 'uuid');
    final flow = (vlessConfig['flow'] as String?) ?? 'xtls-rprx-vision';
    final reality = vlessConfig['reality_opts'] as Map?;

    if (reality == null) {
      throw FormatException(
        'vless_config: отсутствует reality_opts',
      );
    }

    final publicKey = _require(reality, 'public_key');
    final shortId = _require(reality, 'short_id');
    final serverName = (reality['server_name'] as String?) ?? 'www.microsoft.com';
    final fingerprint = (reality['fingerprint'] as String?) ?? 'chrome';

    final tlsBlock = <String, dynamic>{
      'enabled': true,
      'server_name': serverName,
      'utls': <String, dynamic>{
        'enabled': true,
        'fingerprint': fingerprint,
      },
      'reality': <String, dynamic>{
        'enabled': true,
        'public_key': publicKey,
        'short_id': shortId,
      },
    };

    // Fragment: sing-box требует tls.fragment (не top-level outbound).
    final fragment = vlessConfig['fragment'] as Map?;
    if (fragment != null && fragment.isNotEmpty) {
      final fragmentBlock = <String, dynamic>{};
      final packets = fragment['packets'];
      if (packets != null && packets is String && packets.isNotEmpty) {
        fragmentBlock['packets'] = packets;
      }
      final length = fragment['length'];
      if (length != null && length is String && length.isNotEmpty) {
        fragmentBlock['length'] = length;
      }
      final interval = fragment['interval'];
      if (interval != null && interval is String && interval.isNotEmpty) {
        fragmentBlock['interval'] = interval;
      }
      if (fragmentBlock.isNotEmpty) {
        tlsBlock['fragment'] = fragmentBlock;
      }
    }

    final outbound = <String, dynamic>{
      'type': 'vless',
      'tag': 'proxy',
      'server': address,
      'server_port': port,
      'uuid': uuid,
      'flow': flow,
      'tls': tlsBlock,
    };

    return jsonEncode(<String, dynamic>{
      'outbounds': <dynamic>[outbound],
    });
  }

  /// Быстрая проверка: содержит ли конфиг минимально необходимые поля
  /// для подключения по VLESS+Reality.
  static bool isValid(Map<String, dynamic> vlessConfig) {
    final uuid = vlessConfig['uuid'];
    if (uuid == null || (uuid as String).isEmpty) return false;
    final address = vlessConfig['address'];
    if (address == null || (address as String).isEmpty) return false;
    final port = vlessConfig['port'];
    if (port == null) return false;
    final reality = vlessConfig['reality_opts'];
    if (reality == null || reality is! Map) return false;
    final pk = reality['public_key'];
    final sid = reality['short_id'];
    if (pk == null || (pk as String).isEmpty) return false;
    if (sid == null || (sid as String).isEmpty) return false;
    return true;
  }

  static String _require(Map map, String key) {
    final v = map[key];
    if (v == null || (v is String && v.isEmpty)) {
      throw FormatException('vless_config: отсутствует обязательное поле "$key"');
    }
    return v.toString();
  }

  static int _requireInt(Map map, String key) {
    final v = map[key];
    if (v == null) {
      throw FormatException('vless_config: отсутствует обязательное поле "$key"');
    }
    if (v is int) return v;
    return int.tryParse(v.toString()) ??
        (throw FormatException('vless_config: "$key" не является int'));
  }
}
