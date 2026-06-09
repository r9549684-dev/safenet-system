import 'dart:io';
import 'package:flutter/material.dart';
import '../data/repositories/server_repo.dart';
import '../data/repositories/auth_repo.dart';
import '../data/local/secure_storage.dart';
import '../domain/models/server_model.dart';
import '../domain/enums/vpn_status.dart';
import '../services/vpn_service.dart';
import '../core/singbox_vpn.dart';
import '../core/config_cache_service.dart';
import '../core/constants.dart';

// bundleSingbox is defined in singbox_vpn.dart, but we can access it if we import it.

class VpnProvider extends ChangeNotifier {
  final _repo    = ServerRepository();
  final _service = VPNService();

  VpnStatus     _status   = VpnStatus.disconnected;
  ServerModel?  _selected;
  ServerModel?  _active;
  List<ServerModel> _servers = [];
  String?       _error;
  DateTime?   _connectedAt;
  Duration    _elapsed = Duration.zero;
  String?     _proxyAddress;
  bool        _isLoadingServers = false;
  bool        _usingSingbox = false;

  // Traffic stats
  double _rxSpeed = 0;
  double _txSpeed = 0;
  int    _lastRxBytes = 0;
  int    _lastTxBytes = 0;
  int    _pingMs = 0;
  int    _pingTick = 0;

  // Session access control
  bool _isUnlimitedSession = false;  // true — premium/active trial, false — post-trial free

  VpnStatus       get status          => _status;
  ServerModel?    get selected        => _selected;
  ServerModel?    get active          => _active;
  List<ServerModel> get servers       => _servers;
  String?         get error           => _error;
  Duration        get elapsed         => _elapsed;
  String?         get proxyAddress    => _proxyAddress;
  String          get rxSpeedFormatted => _fmtSpeed(_rxSpeed);
  String          get txSpeedFormatted => _fmtSpeed(_txSpeed);
  int             get pingMs           => _pingMs;
  String          get pingFormatted    => '${_pingMs}ms';

  static String _fmtSpeed(double bps) {
    if (bps >= 1048576) return '${(bps / 1048576).toStringAsFixed(1)} MB/s';
    if (bps >= 1024)    return '${(bps / 1024).toStringAsFixed(0)} KB/s';
    return '${bps.toInt()} B/s';
  }

  String get elapsedFormatted {
    final h = _elapsed.inHours.toString().padLeft(2, '0');
    final m = (_elapsed.inMinutes % 60).toString().padLeft(2, '0');
    final s = (_elapsed.inSeconds % 60).toString().padLeft(2, '0');
    return '$h:$m:$s';
  }

  Future<void> loadServers({String? country}) async {
    if (_isLoadingServers) return;
    _isLoadingServers = true;
    try {
      final fetchedServers = await _repo.getServers(country: country);
      _servers = fetchedServers.cast<ServerModel>();
      // Выбираем первый сервер если ещё не выбран
      if (_selected == null && _servers.isNotEmpty) {
        _selected = _servers.first;
      }
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
    } finally {
      _isLoadingServers = false;
    }
  }

  void selectServer(ServerModel s) {
    _selected = s;
    notifyListeners();
  }

  Future<void> connect({
    String? countryCode,
    String mode = 'stealth',
    bool isPremium = false,
    void Function()? onShowPaywall,
  }) async {
    _isUnlimitedSession = isPremium;
    // Авто-регистрация если нет токена
    final token = await SecureStorage.getToken();
    if (token == null) {
        try {
          final authRepo = AuthRepository();
          final lang = await SecureStorage.getLanguage() ?? 'en';
          await authRepo.register(
            country: countryCode ?? 'IR',
            language: lang,
          );
      } catch (e) {
        _status = VpnStatus.error;
        _error  = 'Auth error: $e';
        notifyListeners();
        return;
      }
    }

    // Выбираем сервер если не выбран
    if (_selected == null) {
      if (_servers.isNotEmpty) {
        _selected = _servers.first;
      } else {
        throw 'Список серверов пуст. Проверьте подключение к сети.';
      }
    }

    _status = VpnStatus.connecting;
    _error  = null;
    notifyListeners();

    try {
      // VLESS+Reality+Fragment (sing-box, только China/Iran билд)
      if (mode == 'hybrid' && bundleSingbox) {
        final deviceId = await SecureStorage.getDeviceId() ?? '';
        if (deviceId.isEmpty) throw 'Device ID не найден';

        // Взять конфиг из головы очереди
        var sbConfig = await SingboxVpn.fetchConfig(deviceId);
        if (sbConfig == null) throw 'Не удалось загрузить VLESS конфиг';

        // Попытка подключения + тихий failover
        var ok = await SingboxVpn.start(sbConfig);
        if (!ok) {
          final nextCfg = await SingboxVpn.fetchNextConfig(deviceId);
          if (nextCfg != null) ok = await SingboxVpn.start(nextCfg);
        }
        if (!ok) throw 'Ошибка запуска VLESS+Reality';

        _usingSingbox = true;
        _finishConnect();
        SingboxVpn.consumeAndRefreshCache(deviceId); // fire-and-forget
        return;
      }

      // Получить WG-конфиг с сервера (или из кэша при ошибке сети)
      var wgConfig    = '';
      var showPaywall = false;
      try {
        final cfg = await _repo.connect(_selected!.id);
        wgConfig    = cfg['wg_config'] as String? ?? '';
        showPaywall = cfg['show_paywall'] == true;
        // Сохраняем в кэш для будущих offline-подключений
        if (wgConfig.isNotEmpty) {
          ConfigCacheService.saveWgCache(_selected!.id, wgConfig);
        }
      } catch (_) {
        // Нет сети — пробуем последний рабочий конфиг из кэша
        final cached = await ConfigCacheService.getWgCache(_selected!.id);
        if (cached == null || cached.isEmpty) rethrow;
        wgConfig    = cached;
        showPaywall = false;
      }
      final country = countryCode ?? _selected!.country;

      // Подключиться через StealthVPNService (режим по выбору пользователя)
      final VPNConnectionResult result;
      switch (mode) {
        case 'amnezia':
          result = await _service.connectAmnezia(wgConfig);
          break;
        case 'hybrid':
          result = await _service.connectHybrid(wgConfig: wgConfig);
          break;
        case 'byedpi':
          result = await _service.connectHybrid(
            wgConfig: wgConfig,
            desyncMode: 'disorder',
            splitPosition: 3,
          );
          break;
        case 'stealth':
        default:
          result = await _service.connectAuto(
            wgConfig: wgConfig,
            countryCode: country,
          );
      }

      _proxyAddress = result.proxyAddress;
      _finishConnect();
      if (showPaywall) {
        onShowPaywall?.call();
      }
    } catch (e) {
      _status = VpnStatus.error;
      _error  = e.toString();
      notifyListeners();
    }
  }

  void _finishConnect() {
    _status       = VpnStatus.connected;
    _active       = _selected;
    _connectedAt  = DateTime.now();
    _lastRxBytes  = 0;
    _lastTxBytes  = 0;
    _rxSpeed      = 0;
    _txSpeed      = 0;
    notifyListeners();
    _startTimer();
  }

  Future<void> disconnect() async {
    _status = VpnStatus.disconnecting;
    notifyListeners();
    try {
      if (_usingSingbox) {
        await SingboxVpn.stop();
        _usingSingbox = false;
      } else {
        await _service.disconnect();
      }
    } catch (_) {}
    _status       = VpnStatus.disconnected;
    _active       = null;
    _connectedAt  = null;
    _elapsed      = Duration.zero;
    _proxyAddress = null;
    _rxSpeed      = 0;
    _txSpeed      = 0;
    _lastRxBytes  = 0;
    _lastTxBytes  = 0;
    notifyListeners();
  }

  /// Авто-подключение для пользователей с полным доступом (premium или активный trial).
  Future<void> checkAutoConnect({bool isPremium = false}) async {
    if (!isPremium) return;
    final should = await SecureStorage.getAutoConnect();
    if (should && _status == VpnStatus.disconnected) {
      await connect(isPremium: true);
    }
  }
  static const _postTrialSessionMinutes = 5;

  void _startTimer() {
    Future.doWhile(() async {
      await Future.delayed(const Duration(seconds: 1));
      if (_connectedAt != null && _status == VpnStatus.connected) {
        _elapsed = DateTime.now().difference(_connectedAt!);

        // Лимит 5 минут после окончания trial (free-режим)
        if (!_isUnlimitedSession && _elapsed.inMinutes >= _postTrialSessionMinutes) {
          await _disconnectPostTrialLimit();
          return false;
        }

        // Опрашиваем rx/tx байты, вычисляем скорость (только для WG-режимов)
        try {
          if (!_usingSingbox) {
            final stats = await _service.getStatus();
            final rx = (stats['rx_bytes'] as num?)?.toInt() ?? 0;
            final tx = (stats['tx_bytes'] as num?)?.toInt() ?? 0;
            _rxSpeed = (rx - _lastRxBytes).toDouble().clamp(0, double.infinity);
            _txSpeed = (tx - _lastTxBytes).toDouble().clamp(0, double.infinity);
            _lastRxBytes = rx;
            _lastTxBytes = tx;
          }
        } catch (_) {
          _rxSpeed = 0;
          _txSpeed = 0;
        }

        // Измеряем пинг каждые 10 секунд
        _pingTick++;
        if (_pingTick % 10 == 1) {
          _measurePing();
        }
        notifyListeners();
        return true;
      }
      return false;
    });
  }

  /// Измерение пинга через DNS lookup (быстрый и надёжный способ)
  Future<void> _measurePing() async {
    try {
      final sw = Stopwatch()..start();
      await InternetAddress.lookup('google.com');
      sw.stop();
      _pingMs = sw.elapsedMilliseconds;
    } catch (_) {
      _pingMs = 0;
    }
  }

  /// Автоотключение по истечению 5-минутной post-trial сессии.
  Future<void> _disconnectPostTrialLimit() async {
    try {
      if (_usingSingbox) {
        await SingboxVpn.stop();
        _usingSingbox = false;
      } else {
        await _service.disconnect();
      }
    } catch (_) {}
    _status       = VpnStatus.error;
    _active       = null;
    _connectedAt  = null;
    _elapsed      = Duration.zero;
    _proxyAddress = null;
    _rxSpeed      = 0;
    _txSpeed      = 0;
    _lastRxBytes  = 0;
    _lastTxBytes  = 0;
    _error = '⏱ 5-минутная сессия истекла. Нажмите кнопку выше для переподключения.';
    notifyListeners();
  }
}
