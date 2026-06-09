import '../data/remote/api_client.dart';
import '../data/remote/endpoints.dart';
import '../data/local/secure_storage.dart';

/// Высокоуровневый API-сервис для SafeNet service.
/// Все маршруты привязаны к бэкенду 89.208.107.67:8500.
class ApiService {
  static final ApiService _i = ApiService._();
  factory ApiService() => _i;
  ApiService._();

  final _api = ApiClient();

  // ── Auth ──────────────────────────────────────────────────────────────

  /// Регистрация устройства (POST /auth/device).
  /// Возвращает JWT-токен и сохраняет его в SecureStorage.
  Future<Map<String, dynamic>> registerDevice(String deviceId, {String? country}) async {
    final data = await _api.post<Map<String, dynamic>>(
      Endpoints.register,
      data: {
        'device_id': deviceId,
        if (country != null) 'country': country,
      },
    );
    final token = data['access_token'] as String?;
    if (token != null) {
      await SecureStorage.saveToken(token);
    }
    return data;
  }

  // ── Servers ───────────────────────────────────────────────────────────

  /// Получить список активных серверов (GET /servers).
  Future<Map<String, dynamic>> getServers() async {
    return await _api.get<Map<String, dynamic>>(Endpoints.servers);
  }

  // ── service Connect ───────────────────────────────────────────────────────

  /// Подключиться к service-серверу (POST /service/connect/{server_id}).
  /// Ответ содержит: wg_config, peer_ip, byedpi_profile, mode.
  /// [token] опционален — если null, используется токен из SecureStorage (через interceptor).
  Future<Map<String, dynamic>> connect(int serverId, {String? token}) async {
    return await _api.post<Map<String, dynamic>>(
      Endpoints.connectServer(serverId.toString()),
    );
  }

  // ── Subscription ──────────────────────────────────────────────────────

  /// Статус подписки (GET /users/me).
  /// Возвращает is_premium, premium_until, trial_ends_at.
  Future<Map<String, dynamic>> getSubscription({String? token}) async {
    return await _api.get<Map<String, dynamic>>(Endpoints.me);
  }

  // ── User Profile ──────────────────────────────────────────────────────

  /// Получить текущего пользователя (GET /users/me).
  Future<Map<String, dynamic>> getMe() async {
    return await _api.get<Map<String, dynamic>>(Endpoints.me);
  }
}
