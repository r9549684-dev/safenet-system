import 'dart:async';
import 'dart:io';
import 'bootstrap_service.dart';

/// Типы протоколов для VPN подключения
enum ProtocolType {
  trojan,
  vless,
  awg,
}

/// Результат попытки подключения через Protocol Juggler
class ProtocolJugglerResult {
  final bool connected;
  final ProtocolType? protocol;

  ProtocolJugglerResult({
    required this.connected,
    this.protocol,
  });
}

/// Protocol Juggler — механизм перебора протоколов при health check failure.
/// Расширяет AMO механизмом активного health-probing с failover между протоколами.
class ProtocolJuggler {
  /// Максимальное количество циклов переключения протоколов
  static const int maxFailoverCycles = 3;

  /// SOCKS5 proxy хост и порт (sing-box mixed-inbound)
  static const String proxyHost = '127.0.0.1';
  static const int proxyPort = 2080;

  /// Приоритет протоколов для России (2026):
  /// 1. Trojan — подтверждённо работает через DPI (порт 4443)
  /// 2. VLESS — Reality+Fragment (может блокироваться DPI на порту 8443)
  /// 3. AWG — AmneziaWG (fallback, тоже блокируется DPI в России)
  static const List<ProtocolType> ruProtocolPriority = [
    ProtocolType.trojan,
    ProtocolType.vless,
    ProtocolType.awg,
  ];

  /// Динамические бюджеты готовности по протоколу (оптимизировано для продакшн)
  /// Trojan увеличен до 12s для учёта health check timeout 10s (рекомендация ревизора #29)
  /// VLESS увеличен до 15s для учёта health check timeout 10s (рекомендация ревизора #29)
  static Duration readinessBudget(ProtocolType protocol) {
    switch (protocol) {
      case ProtocolType.trojan:
        return const Duration(seconds: 12); // SOCKS + Trojan + TLS handshake + HTTP = до 10s
      case ProtocolType.vless:
        return const Duration(seconds: 15); // Reality/uTLS медленнее + health check 10s
      case ProtocolType.awg:
        return const Duration(seconds: 3);
    }
  }

  /// L1: Проверка готовности SOCKS5 inbound (порт открыт)
  static Future<bool> isPortOpen(
    String host,
    int port, {
    Duration timeout = const Duration(milliseconds: 300),
  }) async {
    Socket? socket;
    try {
      socket = await Socket.connect(host, port, timeout: timeout);
      return true;
    } on SocketException {
      return false;
    } finally {
      socket?.destroy();
    }
  }

  /// L2: Проверка end-to-end туннеля через generate_204
  /// Использует HTTP proxy (вместо SOCKS5) для совместимости с sing-box mixed-inbound
  /// Timeout увеличен до 10s для VLESS (рекомендация ревизора #29)
  /// Fallback endpoint: cloudflare /cdn-cgi/trace (рекомендация ревизора #23)
  static Future<bool> isTunnelLive(
    String host,
    int port, {
    Duration timeout = const Duration(seconds: 10),
  }) async {
    final stopwatch = Stopwatch()..start();
    final client = HttpClient()..connectionTimeout = timeout;
    client.findProxy = (uri) => 'PROXY $host:$port';
    client.badCertificateCallback = (cert, host, port) => true;
    
    // Primary endpoint: gstatic generate_204
    try {
      print('[HEALTH] Trying gstatic via HTTP proxy $host:$port...');
      final req = await client
          .getUrl(Uri.parse('https://www.gstatic.com/generate_204'))
          .timeout(timeout);
      print('[HEALTH] gstatic request sent in ${stopwatch.elapsedMilliseconds}ms');
      final resp = await req.close().timeout(timeout);
      print('[HEALTH] gstatic response status=${resp.statusCode} in ${stopwatch.elapsedMilliseconds}ms');
      await resp.drain<void>();
      if (resp.statusCode == 204 || resp.statusCode == 200) {
        print('[HEALTH] ✅ gstatic OK in ${stopwatch.elapsedMilliseconds}ms');
        return true;
      }
    } catch (e) {
      print('[HEALTH] ❌ gstatic failed in ${stopwatch.elapsedMilliseconds}ms: $e');
      // Fallback to cloudflare endpoint
    }
    
    // Fallback endpoint: cloudflare trace
    try {
      print('[HEALTH] Trying cloudflare via HTTP proxy $host:$port...');
      final req = await client
          .getUrl(Uri.parse('https://1.1.1.1/cdn-cgi/trace'))
          .timeout(timeout);
      final resp = await req.close().timeout(timeout);
      await resp.drain<void>();
      final ok = resp.statusCode == 200;
      print('[HEALTH] ${ok ? "✅" : "❌"} cloudflare status=${resp.statusCode} in ${stopwatch.elapsedMilliseconds}ms');
      return ok;
    } catch (e) {
      print('[HEALTH] ❌ cloudflare failed in ${stopwatch.elapsedMilliseconds}ms: $e');
      return false;
    } finally {
      client.close(force: true);
    }
  }

  /// Двухуровневый polling readiness check (оптимизировано для продакшн)
  ///
  /// Фаза 1: Ждём открытия порта (L1) с exponential backoff — fast fail если порт не открывается
  /// Фаза 2: Ждём end-to-end туннель (L2) через generate_204
  static Future<bool> waitUntilReady(
    ProtocolType protocol, {
    String host = proxyHost,
    int port = proxyPort,
    Future<bool> Function(String host, int port)? isPortOpenFn,
    Future<bool> Function(String host, int port)? isTunnelLiveFn,
    Duration? budgetOverride, // Для тестов
  }) async {
    final budget = budgetOverride ?? readinessBudget(protocol);
    final deadline = DateTime.now().add(budget);
    var pollInterval = const Duration(milliseconds: 100);
    const maxInterval = Duration(milliseconds: 500);
    final checkPort = isPortOpenFn ?? isPortOpen;
    final checkTunnel = isTunnelLiveFn ?? isTunnelLive;

    // Фаза 1: Ждём открытия порта (L1) — fast fail если порт не открывается
    const portOpenTimeout = Duration(milliseconds: 1000);
    final portDeadline = DateTime.now().add(portOpenTimeout);
    while (DateTime.now().isBefore(portDeadline)) {
      if (await checkPort(host, port)) break;
      await Future.delayed(pollInterval);
      pollInterval = _backoff(pollInterval, maxInterval);
    }
    if (!await checkPort(host, port)) {
      return false; // Fast fail: порт не открылся за 1s
    }

    // Initial delay перед L2 проверкой (рекомендация ревизора #23)
    // Даём время для полного завершения handshake
    await Future.delayed(const Duration(milliseconds: 500));

    // Фаза 2: Ждём end-to-end туннель (L2)
    pollInterval = const Duration(milliseconds: 250);
    while (DateTime.now().isBefore(deadline)) {
      if (await checkTunnel(host, port)) return true;
      await Future.delayed(pollInterval);
    }
    return false;
  }

  /// Exponential backoff для polling
  static Duration _backoff(Duration current, Duration max) {
    final next = current * 1.5;
    return next > max ? max : next;
  }

  /// Polling освобождения порта между stop и start (рекомендация ревизора #19)
  static Future<void> waitPortReleased({
    String host = proxyHost,
    int port = proxyPort,
    Duration timeout = const Duration(seconds: 3),
    Future<bool> Function(String host, int port)? isPortOpenFn,
  }) async {
    final deadline = DateTime.now().add(timeout);
    final checkPort = isPortOpenFn ?? isPortOpen;
    
    // Ждём пока порт освободится
    while (DateTime.now().isBefore(deadline)) {
      if (!await checkPort(host, port)) {
        // Подтверждаем 3 раза подряд что порт действительно свободен
        for (int i = 0; i < 3; i++) {
          await Future.delayed(const Duration(milliseconds: 100));
          if (await checkPort(host, port)) {
            // Порт снова занят — продолжаем ждать
            break;
          }
          if (i == 2) return; // Порт стабилен 300ms — освободился
        }
      }
      await Future.delayed(const Duration(milliseconds: 100));
    }
    // Fallback: ждём TIME_WAIT
    await Future.delayed(const Duration(milliseconds: 500));
  }

  /// Подключается с перебором протоколов при failure.
  ///
  /// [configs] — карта протокол → sing-box JSON конфиг
  /// [startVpn] — функция запуска VPN (возвращает true если процесс стартовал)
  /// [stopVpn] — функция остановки VPN
  /// [checkHealth] — функция проверки реального трафика через туннель
  /// [priority] — порядок перебора протоколов (по умолчанию RU priority)
  /// [isPortOpenFn] — инъекция зависимости для тестирования
  /// [isTunnelLiveFn] — инъекция зависимости для тестирования
  /// [budgetOverride] — переопределение budget для тестирования
  static Future<ProtocolJugglerResult> connectWithFailover({
    required Map<ProtocolType, String> configs,
    required Future<bool> Function(String config) startVpn,
    required Future<void> Function() stopVpn,
    required Future<bool> Function() checkHealth,
    List<ProtocolType>? priority,
    Future<bool> Function(String host, int port)? isPortOpenFn,
    Future<bool> Function(String host, int port)? isTunnelLiveFn,
    Duration? budgetOverride, // Для тестов
  }) async {
    final protocolOrder = priority ?? ruProtocolPriority;
    int failoverCount = 0;

    for (final protocol in protocolOrder) {
      if (failoverCount >= maxFailoverCycles) {
        print('[JUGGLER] 🛑 Max failover cycles ($maxFailoverCycles) reached');
        break;
      }

      final config = configs[protocol];
      if (config == null) {
        print('[JUGGLER] ⏭️ $protocol — config missing, skipping');
        continue;
      }

      print('[JUGGLER] 🔄 Trying $protocol...');
      print('[JUGGLER] 📄 Config for $protocol: ${config.substring(0, config.length > 200 ? 200 : config.length)}...');

      try {
        final started = await startVpn(config);
        if (!started) {
          print('[JUGGLER] ❌ $protocol start() returned false');
          failoverCount++;
          continue;
        }

        print('[JUGGLER] 🔍 Running readiness check for $protocol...');
        final healthy = await waitUntilReady(
          protocol,
          isPortOpenFn: isPortOpenFn,
          isTunnelLiveFn: isTunnelLiveFn,
          budgetOverride: budgetOverride,
        );

        if (healthy) {
          print('[JUGGLER] ✅ $protocol connected and healthy');
          return ProtocolJugglerResult(
            connected: true,
            protocol: protocol,
          );
        }

        print('[FAILOVER] ${protocol.name.toUpperCase()}→NEXT reason=health_timeout');
        await stopVpn();
        await Future.delayed(const Duration(milliseconds: 500)); // Даём время sing-box полностью остановиться
        await waitPortReleased(isPortOpenFn: isPortOpenFn);
        failoverCount++;
      } catch (e) {
        print('[JUGGLER] ❌ $protocol exception: $e');
        try {
          await stopVpn();
          await waitPortReleased(isPortOpenFn: isPortOpenFn);
        } catch (_) {}
        failoverCount++;
      }
    }

    print('[JUGGLER] ❌ All protocols failed');
    
    print('[JUGGLER] 🆘 Attempting bootstrap fallback...');
    final bootstrapConfig = await BootstrapService.loadBootstrapConfig();
    if (bootstrapConfig != null) {
      print('[JUGGLER] 📦 Bootstrap config loaded, trying to connect...');
      try {
        final started = await startVpn(bootstrapConfig);
        if (started) {
          print('[JUGGLER] 🔍 Running readiness check for bootstrap...');
          final healthy = await waitUntilReady(
            ProtocolType.trojan,
            isPortOpenFn: isPortOpenFn,
            isTunnelLiveFn: isTunnelLiveFn,
            budgetOverride: budgetOverride,
          );
          
          if (healthy) {
            print('[JUGGLER] ✅ Bootstrap connected and healthy');
            return ProtocolJugglerResult(
              connected: true,
              protocol: ProtocolType.trojan,
            );
          }
          
          print('[JUGGLER] ❌ Bootstrap health check failed');
          await stopVpn();
        } else {
          print('[JUGGLER] ❌ Bootstrap start() returned false');
        }
      } catch (e) {
        print('[JUGGLER] ❌ Bootstrap exception: $e');
        try {
          await stopVpn();
        } catch (_) {}
      }
    } else {
      print('[JUGGLER] ❌ Bootstrap config not available');
    }
    
    return ProtocolJugglerResult(
      connected: false,
      protocol: null,
    );
  }
}
