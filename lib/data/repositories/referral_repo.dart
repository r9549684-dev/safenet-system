import '../remote/api_client.dart';
import '../remote/endpoints.dart';

class ReferralRepository {
  final _api = ApiClient();

  Future<Map<String, dynamic>> getStats() =>
      _api.get<Map<String, dynamic>>(Endpoints.referralStats);

  /// Defensive parsing: backend по конвенции возвращает wrapped Map
  /// {"rewards": [...]} или {"transactions": [...]} — извлекаем массив безопасно.
  Future<List> getRewards() async {
    try {
      final raw = await _api.get<Map<String, dynamic>>(Endpoints.referralRewards);
      if (raw is Map) {
        for (final key in ['rewards', 'transactions', 'data']) {
          if (raw[key] is List) return raw[key] as List;
        }
      }
      if (raw is List) return raw;
      return [];
    } catch (_) {
      return []; // endpoint может отсутствовать на бэкенде — не критично
    }
  }

  Future<Map<String, dynamic>> requestPayout(int telegramUserId) =>
      _api.post<Map<String, dynamic>>(
        Endpoints.requestPayout,
        params: {'telegram_user_id': telegramUserId},
      );
}
