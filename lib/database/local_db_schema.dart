/// Схема локальной базы данных SafeNet (SQLite).
/// Поддержка адаптивности под страны и Памяти Решений (Decision Memory).
/// Используется как справочник для миграций или инициализации sqflite/hive.
abstract class LocalDbSchema {
  // -------------------------------------------------------------------------
  // Таблица серверов (Servers)
  // Хранит основные данные сервера + JSON-дамп мета-информации.
  // -------------------------------------------------------------------------
  static const String createServersTable = '''
    CREATE TABLE IF NOT EXISTS servers (
      id TEXT PRIMARY KEY,
      country TEXT NOT NULL,
      name TEXT NOT NULL,
      host TEXT NOT NULL,
      port INTEGER NOT NULL,
      is_active INTEGER DEFAULT 1,
      priority INTEGER DEFAULT 0,
      meta TEXT -- JSON-строка с geo_instructions и другими параметрами
    );
  ''';

  // -------------------------------------------------------------------------
  // Таблица геособенностей (Geo Instructions)
  // Хранит специфические параметры обхода DPI для конкретных стран.
  // -------------------------------------------------------------------------
  static const String createGeoInstructionsTable = '''
    CREATE TABLE IF NOT EXISTS geo_instructions (
      country_code TEXT PRIMARY KEY,          -- 'IR', 'AE', 'CN', 'RU'
      tls_fingerprint TEXT,                   -- Подмена TLS-отпечатка (напр., 'chrome_120')
      fragment_enabled INTEGER DEFAULT 0,     -- 1 = включена фрагментация пакетов
      fragment_size TEXT,                     -- Настройки размера фрагмента (напр., '10-30')
      fragment_ttl INTEGER,                   -- TTL фрагментов
      bypass_mode TEXT,                       -- Режим обхода: 'singbox', 'byedpi', 'amnezia'
      notes TEXT,                             -- Дополнительные комментарии (напр., 'BGP-shutdown с 28.02.2026')
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
  ''';

  // -------------------------------------------------------------------------
  // Таблица Памяти Решений (Decision Memory)
  // Фиксирует историю подключений для обучения предиктивного движка.
  // -------------------------------------------------------------------------
  static const String createDecisionMemoryTable = '''
    CREATE TABLE IF NOT EXISTS decision_memory (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      country_code TEXT NOT NULL,             -- Страна контекста
      network_type TEXT,                      -- Тип сети: 'WiFi', 'Cellular', 'Iran_BGP'
      tactic_used TEXT NOT NULL,              -- Примененная тактика: 'VLESS_Reality_Fragment', 'AmneziaWG'
      result TEXT NOT NULL,                   -- Результат: 'SUCCESS', 'TIMEOUT', 'BLOCKED'
      handshake_time_ms INTEGER,              -- Время рукопожатия (мс)
      confidence_score REAL,                  -- Индекс уверенности предиктивного движка (0.0 - 1.0)
      is_shadow_mode INTEGER DEFAULT 1,       -- 1 = режим Shadow (SHADOW:), 0 = реальное применение
      server_id INTEGER,                      -- ID сервера, к которому применялась тактика
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
  ''';

  // -------------------------------------------------------------------------
  // Индексы для ускорения аналитических выборок
  // -------------------------------------------------------------------------
  static const String createDecisionMemoryIndexes = '''
    CREATE INDEX IF NOT EXISTS idx_decision_country ON decision_memory(country_code);
    CREATE INDEX IF NOT EXISTS idx_decision_result ON decision_memory(result);
    CREATE INDEX IF NOT EXISTS idx_decision_shadow ON decision_memory(is_shadow_mode, created_at);
  ''';

  // -------------------------------------------------------------------------
  // Полный набор команд инициализации
  // -------------------------------------------------------------------------
  static List<String> get allCreationQueries => [
        createServersTable,
        createGeoInstructionsTable,
        createDecisionMemoryTable,
        createDecisionMemoryIndexes,
      ];
}

/// Модели данных, соответствующие схеме БД (для типизированной работы в Dart).
class GeoInstruction {
  final String countryCode;
  final String? tlsFingerprint;
  final bool fragmentEnabled;
  final String? fragmentSize;
  final int? fragmentTtl;
  final String? bypassMode;
  final String? notes;

  GeoInstruction({
    required this.countryCode,
    this.tlsFingerprint,
    this.fragmentEnabled = false,
    this.fragmentSize,
    this.fragmentTtl,
    this.bypassMode,
    this.notes,
  });

  factory GeoInstruction.fromMap(Map<String, dynamic> map) {
    return GeoInstruction(
      countryCode: map['country_code'] as String,
      tlsFingerprint: map['tls_fingerprint'] as String?,
      fragmentEnabled: (map['fragment_enabled'] as int) == 1,
      fragmentSize: map['fragment_size'] as String?,
      fragmentTtl: map['fragment_ttl'] as int?,
      bypassMode: map['bypass_mode'] as String?,
      notes: map['notes'] as String?,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'country_code': countryCode,
      'tls_fingerprint': tlsFingerprint,
      'fragment_enabled': fragmentEnabled ? 1 : 0,
      'fragment_size': fragmentSize,
      'fragment_ttl': fragmentTtl,
      'bypass_mode': bypassMode,
      'notes': notes,
    };
  }
}

class DecisionRecord {
  final int? id;
  final String countryCode;
  final String? networkType;
  final String tacticUsed;
  final String result; // 'SUCCESS', 'TIMEOUT', 'BLOCKED'
  final int? handshakeTimeMs;
  final double? confidenceScore;
  final bool isShadowMode;
  final int? serverId;
  final DateTime createdAt;

  DecisionRecord({
    this.id,
    required this.countryCode,
    this.networkType,
    required this.tacticUsed,
    required this.result,
    this.handshakeTimeMs,
    this.confidenceScore,
    this.isShadowMode = true, // По умолчанию Shadow Mode (Этап 4 ANO)
    this.serverId,
    DateTime? createdAt,
  }) : createdAt = createdAt ?? DateTime.now();

  factory DecisionRecord.fromMap(Map<String, dynamic> map) {
    return DecisionRecord(
      id: map['id'] as int?,
      countryCode: map['country_code'] as String,
      networkType: map['network_type'] as String?,
      tacticUsed: map['tactic_used'] as String,
      result: map['result'] as String,
      handshakeTimeMs: map['handshake_time_ms'] as int?,
      confidenceScore: (map['confidence_score'] as num?)?.toDouble(),
      isShadowMode: (map['is_shadow_mode'] as int) == 1,
      serverId: map['server_id'] as int?,
      createdAt: DateTime.parse(map['created_at'] as String),
    );
  }

  Map<String, dynamic> toMap() {
    return {
      if (id != null) 'id': id,
      'country_code': countryCode,
      'network_type': networkType,
      'tactic_used': tacticUsed,
      'result': result,
      'handshake_time_ms': handshakeTimeMs,
      'confidence_score': confidenceScore,
      'is_shadow_mode': isShadowMode ? 1 : 0,
      'server_id': serverId,
      'created_at': createdAt.toIso8601String(),
    };
  }
}
