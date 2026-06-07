import 'dart:convert';
import '../../database/local_db_schema.dart';

/// Расширенная доменная модель сервера SafeNet.
/// Является единым источником правды о сервере, включая специфические
/// гео-инструкции для обхода блокировок (фрагментация, TLS fingerprint).
class ServerModel {
  final String id;
  final String country;
  final String name;
  final String host; // IP или домен
  final int port;
  final bool isActive;
  final int priority;
  final Map<String, dynamic>? meta; // Дополнительная метаинформация (например, geo_instructions)
  
  // Вычисленные поля для UI
  final GeoInstruction? geoInstructions;

  const ServerModel({
    required this.id,
    required this.country,
    required this.name,
    required this.host,
    required this.port,
    required this.isActive,
    required this.priority,
    this.meta,
    this.geoInstructions,
  });

  factory ServerModel.fromJson(Map<String, dynamic> json) {
    GeoInstruction? geo;
    if (json['geo_instructions'] != null && json['geo_instructions'] is Map) {
      geo = GeoInstruction.fromMap(Map<String, dynamic>.from(json['geo_instructions']));
    } else if (json['meta'] != null && json['meta']['geo_instructions'] != null) {
      geo = GeoInstruction.fromMap(Map<String, dynamic>.from(json['meta']['geo_instructions']));
    }

    return ServerModel(
      id: json['id'].toString(),
      country: json['country'].toString().toUpperCase(),
      name: json['name'] ?? 'Unknown',
      host: json['host'] ?? json['ip'] ?? '',
      port: int.tryParse(json['port'].toString()) ?? 51820,
      isActive: json['is_active'] ?? json['isActive'] ?? true,
      priority: int.tryParse(json['priority'].toString()) ?? 0,
      meta: json['meta'] != null ? Map<String, dynamic>.from(json['meta']) : null,
      geoInstructions: geo,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'country': country,
      'name': name,
      'host': host,
      'port': port,
      'is_active': isActive ? 1 : 0,
      'priority': priority,
      if (meta != null) 'meta': jsonEncode(meta),
    };
  }

  String get flag => {
    'TR': '🇹🇷', 'EG': '🇪🇬', 'PK': '🇵🇰',
    'ID': '🇮🇩', 'AE': '🇦🇪', 'VE': '🇻🇪', 'SA': '🇸🇦',
    'IR': '🇮🇷', 'CN': '🇨🇳', 'RU': '🇷🇺',
  }[country] ?? '🌍';

  String get audienceName => const {
    'TR': 'Турция',
    'AE': 'ОАЭ',
    'EG': 'Египет',
    'SA': 'Саудовская Аравия',
    'PK': 'Пакистан',
    'ID': 'Индонезия',
    'VE': 'Венесуэла',
    'IR': 'Иран',
    'CN': 'Китай',
    'RU': 'Россия',
  }[country] ?? country;

  /// Определяет, включена ли фрагментация для этого сервера (через geo_instructions или meta)
  bool get isFragmentationEnabled {
    if (geoInstructions?.fragmentEnabled == true) return true;
    if (meta?['fragmentation_enabled'] == true) return true;
    return false;
  }

  /// Режим обхода по умолчанию для этого сервера
  String get bypassMode => geoInstructions?.bypassMode ?? meta?['bypass_mode'] ?? 'default';
}
