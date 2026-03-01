import 'package:flutter/services.dart';
import 'package:uuid/uuid.dart';
import '../local/secure_storage.dart';
import '../remote/api_client.dart';
import '../remote/endpoints.dart';
import '../../domain/models/user.dart';

class AuthRepository {
  final _api = ApiClient();

  Future<String> getOrCreateDeviceId() async {
    try {
      // Возвращаем сохранённый ID если уже есть и не пустой
      final saved = await SecureStorage.getDeviceId();
      if (saved != null && saved.isNotEmpty) return saved;

      // При первой установке — генерируем уникальный UUID и сохраняем навсегда
      final id = const Uuid().v4();
      try {
        await SecureStorage.saveDeviceId(id);
      } on PlatformException {
        // Keystore недоступен — ID не сохранится между сессиями,
        // но регистрация в этот раз пройдёт
      }
      return id;
    } on PlatformException {
      // SecureStorage полностью недоступен — генерируем одноразовый UUID
      return const Uuid().v4();
    }
  }

  Future<User> register({
    required String country,
    required String language,
    String? referralCode,
  }) async {
    final deviceId = await getOrCreateDeviceId();
    final data = await _api.post<Map<String, dynamic>>(
      Endpoints.register,
      data: {
        'device_id':        deviceId,
        'country':          country,
        'language':         language,
        'referred_by_code': referralCode,
      },
    );
    await SecureStorage.saveToken(data['access_token']);
    await SecureStorage.saveCountry(country);
    await SecureStorage.saveLanguage(language);
    return User.fromJson(data['user']);
  }

  Future<User?> tryAutoLogin() async {
    final token = await SecureStorage.getToken();
    if (token == null) return null;
    try {
      final data = await _api.get<Map<String, dynamic>>(Endpoints.me);
      return User.fromJson(data);
    } catch (_) {
      return null;
    }
  }

  Future<void> logout() => SecureStorage.clearAll();
}
