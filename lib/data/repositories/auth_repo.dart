import 'dart:io';
import 'package:flutter/services.dart';
import 'package:uuid/uuid.dart';
import '../local/secure_storage.dart';
import '../remote/api_client.dart';
import '../remote/endpoints.dart';
import '../../domain/models/user.dart';

class AuthRepository {
  final _api = ApiClient();

  // MethodChannel уже объявлен в MainActivity.kt — переиспользуем
  static const _channel = MethodChannel('com.safenet.vpn/methods');

  Future<String> getOrCreateDeviceId() async {
    try {
      // 1. Возвращаем сохранённый ID (backward-compatible для уже установленных)
      final saved = await SecureStorage.getDeviceId();
      if (saved != null && saved.isNotEmpty) return saved;

      // 2. Android: берём ANDROID_ID — аппаратный ID, переживает переустановку
      //    (меняется только при factory reset или смене пользователя)
      if (Platform.isAndroid) {
        try {
          final androidId = await _channel.invokeMethod<String>('getAndroidId');
          if (androidId != null && androidId.isNotEmpty && androidId != '0000000000000000') {
            try { await SecureStorage.saveDeviceId(androidId); } on PlatformException { /* ignore */ }
            return androidId;
          }
        } on PlatformException { /* fall through */ }
      }

      // 3. Fallback (iOS / ANDROID_ID недоступен): случайный UUID
      final id = const Uuid().v4();
      try {
        await SecureStorage.saveDeviceId(id);
      } on PlatformException { /* Keystore недоступен — OK */ }
      return id;
    } on PlatformException {
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
