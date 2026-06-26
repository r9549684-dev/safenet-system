import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:safenet_vpn/core/singbox_proxy_test.dart';
import 'package:safenet_vpn/core/trojan_to_singbox.dart';

/// Тест Trojan через proxy mode (без VPN TUN).
/// Запускает sing-box как HTTP/SOCKS5 proxy и проверяет подключение через Trojan.
class TrojanProxyTest {
  static const String _tag = 'TrojanProxyTest';

  /// Тест Trojan подключения через proxy mode.
  /// [trojanConfig] - конфиг из бэкенда (address, port, password, sni, insecure)
  static Future<bool> testTrojanConnection(Map<String, dynamic> trojanConfig) async {
    debugPrint('[$_tag] === НАЧАЛО ТЕСТА TROJAN ===');
    debugPrint('[$_tag] Конфиг: ${trojanConfig.keys.toList()}');

    if (!TrojanSingboxConverter.isValid(trojanConfig)) {
      debugPrint('[$_tag] ОШИБКА: невалидный Trojan конфиг');
      return false;
    }

    try {
      // 1. Конвертируем Trojan в sing-box JSON
      final singboxJson = TrojanSingboxConverter.toSingboxJson(trojanConfig);
      debugPrint('[$_tag] Sing-box JSON: ${singboxJson.substring(0, singboxJson.length.clamp(0, 200))}...');

      // 2. Запускаем proxy mode
      debugPrint('[$_tag] Запуск proxy mode...');
      final result = await SingboxProxyTest.startTrojanProxy(singboxJson);
      debugPrint('[$_tag] Proxy запущен: $result');

      // 3. Ждём готовности proxy
      debugPrint('[$_tag] Ожидание готовности proxy (3 сек)...');
      await Future.delayed(const Duration(seconds: 3));

      // 4. Проверяем статус
      final running = await SingboxProxyTest.isRunning();
      debugPrint('[$_tag] Proxy running: $running');

      if (!running) {
        debugPrint('[$_tag] ОШИБКА: proxy не запустился');
        return false;
      }

      // 5. Тестируем HTTP запрос через proxy
      debugPrint('[$_tag] Тест HTTP запроса через proxy 127.0.0.1:2080...');
      final httpClient = HttpClient();
      httpClient.findProxy = (uri) => 'PROXY 127.0.0.1:2080';
      httpClient.badCertificateCallback = (cert, host, port) => true;

      try {
        final request = await httpClient.getUrl(Uri.parse('https://www.google.com'));
        final response = await request.close();
        debugPrint('[$_tag] HTTP статус: ${response.statusCode}');

        if (response.statusCode == 200 || response.statusCode == 301 || response.statusCode == 302) {
          debugPrint('[$_tag] ✅ TROJAN РАБОТАЕТ! HTTP запрос прошёл через proxy.');
          return true;
        } else {
          debugPrint('[$_tag] ❌ HTTP запрос вернул статус ${response.statusCode}');
          return false;
        }
      } catch (e) {
        debugPrint('[$_tag] ❌ ОШИБКА HTTP запроса: $e');
        return false;
      } finally {
        httpClient.close();
      }
    } catch (e) {
      debugPrint('[$_tag] ❌ ОШИБКА ТЕСТА: $e');
      return false;
    } finally {
      // 6. Останавливаем proxy
      debugPrint('[$_tag] Остановка proxy...');
      await SingboxProxyTest.stop();
      debugPrint('[$_tag] === КОНЕЦ ТЕСТА TROJAN ===');
    }
  }

  /// Тест Trojan с конкретным конфигом (для отладки).
  static Future<bool> testWithExplicitConfig({
    required String address,
    required int port,
    required String password,
    String sni = 'www.microsoft.com',
    bool insecure = true,
  }) {
    return testTrojanConnection({
      'address': address,
      'port': port,
      'password': password,
      'sni': sni,
      'insecure': insecure,
    });
  }
}
