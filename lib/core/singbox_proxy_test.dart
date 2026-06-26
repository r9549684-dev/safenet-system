import 'package:flutter/services.dart';
import 'package:flutter/foundation.dart';

/// E2E test launcher for sing-box as HTTP/SOCKS5 proxy (no VpnService).
/// Calls the native [SingboxProxyService] via MethodChannel.
class SingboxProxyTest {
  static const _channel = MethodChannel('com.safenet.vpn/singbox_proxy');

  static Future<Map<String, dynamic>> start(String outboundsJson) async {
    final res = await _channel.invokeMethod<Map>('start', {'config': outboundsJson});
    return Map<String, dynamic>.from(res ?? {});
  }

  static Future<void> stop() => _channel.invokeMethod('stop');

  static Future<bool> isRunning() async {
    final res = await _channel.invokeMethod<Map>('status');
    return res?['running'] == true;
  }

  /// Start proxy with a VLESS config (the full sing-box outbounds JSON).
  /// [outboundsJson] should contain the "outbounds" array already built by vless_to_singbox.dart
  static Future<Map<String, dynamic>> startVlessProxy(String outboundsJson) async {
    debugPrint('[SingboxProxyTest] starting proxy...');
    try {
      final result = await start(outboundsJson);
      debugPrint('[SingboxProxyTest] proxy started: $result');
      return result;
    } catch (e) {
      debugPrint('[SingboxProxyTest] ERROR: $e');
      rethrow;
    }
  }

  /// Start proxy with a Trojan config (the full sing-box outbounds JSON).
  /// [outboundsJson] should contain the "outbounds" array already built by trojan_to_singbox.dart
  static Future<Map<String, dynamic>> startTrojanProxy(String outboundsJson) async {
    debugPrint('[SingboxProxyTest] starting Trojan proxy...');
    try {
      final result = await start(outboundsJson);
      debugPrint('[SingboxProxyTest] Trojan proxy started: $result');
      return result;
    } catch (e) {
      debugPrint('[SingboxProxyTest] Trojan ERROR: $e');
      rethrow;
    }
  }
}
