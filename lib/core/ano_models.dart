/// Модели данных для SafeNet ANO (Active Network Optimization).
/// Уровень 0: Телеметрия и State Machine.

class ScoutMetrics {
  final String serverId;
  final double rttMs;
  final double jitterMs;
  final double lossPct;
  final double throughputKbps;
  final DateTime timestamp;

  ScoutMetrics({
    required this.serverId,
    required this.rttMs,
    required this.jitterMs,
    required this.lossPct,
    required this.throughputKbps,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();

  Map<String, dynamic> toJson() => {
        'server_id': serverId,
        'rtt_ms': rttMs,
        'jitter_ms': jitterMs,
        'loss_pct': lossPct,
        'throughput_kbps': throughputKbps,
        'timestamp': timestamp.toIso8601String(),
      };
}

class AnoRecommendation {
  final String serverId;
  final String? recommendedAction; // например, "switch_to_alternative"
  final double confidence;
  final double avgDowntime;
  final bool isShadow; // true, если рекомендация только для сбора данных

  AnoRecommendation({
    required this.serverId,
    this.recommendedAction,
    required this.confidence,
    required this.avgDowntime,
    required this.isShadow,
  });

  factory AnoRecommendation.fromJson(Map<String, dynamic> json) {
    return AnoRecommendation(
      serverId: json['server_id'] as String,
      recommendedAction: json['recommended_action'] as String?,
      confidence: (json['confidence'] as num).toDouble(),
      avgDowntime: (json['avg_downtime'] as num).toDouble(),
      isShadow: json['is_shadow'] as bool,
    );
  }
}

enum HandoverState {
  connected,
  handoverInit,
  preFlight,
  drainOld,
  coolDown,
}