import 'package:flutter/material.dart';
import '../data/repositories/server_repo.dart';
import '../data/repositories/auth_repo.dart';
import '../data/local/secure_storage.dart';
import '../domain/models/server.dart';
import '../domain/enums/vpn_status.dart';
import '../services/vpn_service.dart';

class VpnProvider extends ChangeNotifier {
  final _repo    = ServerRepository();
  final _service = VPNService();

  VpnStatus   _status   = VpnStatus.disconnected;
  VpnServer?  _selected;
  VpnServer?  _active;
  List<VpnServer> _servers = [];
  String?     _error;
  DateTime?   _connectedAt;
  Duration    _elapsed = Duration.zero;
  String?     _proxyAddress;
  bool        _isLoadingServers = false;

  // Traffic stats
  double _rxSpeed = 0;
  double _txSpeed = 0;
  int    _lastRxBytes = 0;
  int    _lastTxBytes = 0;

  // Session access control
  bool _isUnlimitedSession = false;  // true — premium/active trial, false — post-trial free

  VpnStatus       get status          => _status;
  VpnServer?      get selected        => _selected;
  VpnServer?      get active          => _active;
  List<VpnServer> get servers         => _servers;
  String?         get error           => _error;
  Duration        get elapsed         => _elapsed;
  String?         get proxyAddress    => _proxyAddress;
  String          get rxSpeedFormatted => _fmtSpeed(_rxSpeed);
  String          get txSpeedFormatted => _fmtSpeed(_txSpeed);

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
      _servers = await _repo.getServers(country: country);
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

  void selectServer(VpnServer s) {
    _selected = s;
    notifyListeners();
  }

  Future<void> connect({String? countryCode, String mode = 'stealth', bool isPremium = false}) async {
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
        _selected = VpnServer.defaults.first;
      }
    }

    _status = VpnStatus.connecting;
    _error  = null;
    notifyListeners();

    try {
      // Получить WG-конфиг с сервера
      final cfg = await _repo.connect(_selected!.id);
      final wgConfig = cfg['wg_config'] as String? ?? '';
      final country  = countryCode ?? _selected!.country;

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
      await _service.disconnect();
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

        // Опрашиваем rx/tx байты, вычисляем скорость
        try {
          final stats = await _service.getStatus();
          final rx = (stats['rx_bytes'] as num?)?.toInt() ?? 0;
          final tx = (stats['tx_bytes'] as num?)?.toInt() ?? 0;
          _rxSpeed = (rx - _lastRxBytes).toDouble().clamp(0, double.infinity);
          _txSpeed = (tx - _lastTxBytes).toDouble().clamp(0, double.infinity);
          _lastRxBytes = rx;
          _lastTxBytes = tx;
        } catch (_) {
          _rxSpeed = 0;
          _txSpeed = 0;
        }
        notifyListeners();
        return true;
      }
      return false;
    });
  }

  /// Автоотключение по истечению 5-минутной post-trial сессии.
  Future<void> _disconnectPostTrialLimit() async {
    try { await _service.disconnect(); } catch (_) {}
    _status       = VpnStatus.error;
    _active       = null;
    _connectedAt  = null;
    _elapsed      = Duration.zero;
    _proxyAddress = null;
    _rxSpeed      = 0;
    _txSpeed      = 0;
    _lastRxBytes  = 0;
    _lastTxBytes  = 0;
    _error = '⏱ 5-мин сессия после триала завершена. Нажмите RETRY для переподключения.';
    notifyListeners();
  }
}
