import '../remote/api_client.dart';
import '../remote/endpoints.dart';
import '../../domain/models/server.dart';
import '../../domain/models/server_model.dart';

class ServerRepository {
  final _api = ApiClient();

  Future<List<ServerModel>> getServers({String? country}) async {
    // Backend возвращает {"servers": [...]} — Map, а не List
    final raw = await _api.get<Map<String, dynamic>>(
      Endpoints.servers,
      params: country != null ? {'country': country} : null,
    );
    final list = raw['servers'] as List;
    return list
        .map((j) => ServerModel.fromJson(Map<String, dynamic>.from(j as Map)))
        .toList();
  }

  Future<VpnServer> getRecommended() async {
    final data = await _api.get<Map<String, dynamic>>(Endpoints.recommendedServer);
    return VpnServer.fromJson(data);
  }

  Future<Map<String, dynamic>> connect(String serverId) async {
    return _api.post<Map<String, dynamic>>(Endpoints.connectServer(serverId));
  }

  Future<Map<String, dynamic>> redeemPromo(String code) async {
    return _api.post<Map<String, dynamic>>(
      Endpoints.redeemPromo,
      data: {'code': code.trim().toUpperCase()},
    );
  }

  // ─ SafeNet AMO: Seamless Failover ──────────────────────────────────────

  Future<List<Map<String, dynamic>>> getConnectionPool() async {
    // Backend VpnPoolResponse возвращает {"configs": [...]} — Map, а не List
    final raw = await _api.post<Map<String, dynamic>>(Endpoints.connectionPool);
    final list = raw['configs'] as List? ?? [];
    return list
        .map((e) => Map<String, dynamic>.from(e as Map))
        .toList();
  }

  Future<bool> reportBlockedConfig(String allocatedIp) async {
    try {
      await _api.post(Endpoints.reportBlocked, data: {'allocated_ip': allocatedIp});
      return true;
    } catch (_) {
      return false; // Fire-and-forget, не критично если не отправилось
    }
  }
}
