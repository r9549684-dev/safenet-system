import 'dart:convert';
import 'package:flutter/services.dart';
import 'package:flutter/foundation.dart';

class BootstrapService {
  static const String _bootstrapAsset = 'assets/bootstrap_config.json';
  
  static Future<String?> loadBootstrapConfig() async {
    try {
      final configJson = await rootBundle.loadString(_bootstrapAsset);
      final config = json.decode(configJson) as Map<String, dynamic>;
      
      debugPrint('[BootstrapService] Loaded bootstrap config: ${config['outbounds'][0]['server']}:${config['outbounds'][0]['server_port']}');
      
      return configJson;
    } catch (e) {
      debugPrint('[BootstrapService] Failed to load bootstrap config: $e');
      return null;
    }
  }
  
  static Future<Map<String, dynamic>?> loadBootstrapConfigAsMap() async {
    try {
      final configJson = await rootBundle.loadString(_bootstrapAsset);
      return json.decode(configJson) as Map<String, dynamic>;
    } catch (e) {
      debugPrint('[BootstrapService] Failed to parse bootstrap config: $e');
      return null;
    }
  }
}
