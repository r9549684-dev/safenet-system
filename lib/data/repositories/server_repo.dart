import '../remote/api_client.dart';
import '../remote/endpoints.dart';
import '../../domain/models/server.dart';

class ServerRepository {
  final _api = ApiClient();

  Future<List<VpnServer>> getServers({String? country}) async {
    final data = await _api.get<List>(
      Endpoints.servers,
      params: country != null ? {'country': country} : null,
    );
    return data.map((j) => VpnServer.fromJson(j)).toList();
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
}
