"""
SafeNet ANO: Node Ranking Engine
Реализует эволюционное ранжирование узлов на основе метрик скаута.
"""
import math
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class NodeMetrics:
    node_id: str
    rtt_avg: float       # мс
    jitter: float        # мс
    loss_pct: float      # %
    throughput_kbps: float # КБ/с
    life_hours: float    # часов без блокировок

class NodeRanker:
    @staticmethod
    def calculate_rating(metrics: NodeMetrics) -> float:
        """
        Расчет эволюционного рейтинга узла по формуле ANO v1.0.0.
        Возвращает float рейтинг.
        """
        # 1. Базовый скоринг
        base_score = 1000.0 / (metrics.rtt_avg + 1.0)
        
        # 2. Множитель скорости (логарифмическое насыщение)
        speed_multiplier = 1.0 + math.log(1.0 + (metrics.throughput_kbps / 1000.0))
        
        # 3. Штрафы
        loss_penalty = math.exp(-0.15 * metrics.loss_pct)
        jitter_penalty = 1.0 / (1.0 + (metrics.jitter / 30.0))
        life_penalty = min(metrics.life_hours / 48.0, 1.0)
        
        # Итоговый сырой рейтинг
        rating = base_score * speed_multiplier * loss_penalty * jitter_penalty * life_penalty
        
        # 4. Критические триггеры (применяются ПОСЛЕ расчета)
        if metrics.loss_pct > 30.0:
            rating *= 0.1  # Принудительная чёрная зона
        elif metrics.loss_pct > 15.0:
            rating *= 0.3
        elif metrics.jitter > 100.0:
            rating *= 0.5
            
        return round(rating, 2)

    @staticmethod
    def get_zone(rating: float) -> str:
        """Определение цветовой зоны по рейтингу."""
        if rating > 15.0:
            return "GREEN"
        elif rating >= 5.0:
            return "YELLOW"
        elif rating >= 2.0:
            return "RED"
        else:
            return "BLACK"

    @classmethod
    def select_best_node(cls, nodes_data: List[Dict[str, Any]], min_rating: float = 15.0) -> Optional[Dict[str, Any]]:
        """
        Выбирает лучший узел из списка, отфильтровывая те, что ниже min_rating (по умолчанию Зеленая зона).
        Возвращает словарь с данными узла или None, если подходящих нет.
        """
        scored_nodes = []
        
        for node in nodes_data:
            metrics = NodeMetrics(
                node_id=node.get("id"),
                rtt_avg=float(node.get("rtt_avg", 999.0)),
                jitter=float(node.get("jitter", 100.0)),
                loss_pct=float(node.get("loss_pct", 50.0)),
                throughput_kbps=float(node.get("throughput_kbps", 10.0)),
                life_hours=float(node.get("life_hours", 1.0))
            )
            
            rating = cls.calculate_rating(metrics)
            zone = cls.get_zone(rating)
            
            scored_nodes.append({
                **node,
                "ano_rating": rating,
                "ano_zone": zone
            })
            
        # Фильтруем только допустимые зоны (GREEN по умолчанию)
        valid_nodes = [n for n in scored_nodes if n["ano_rating"] >= min_rating]
        
        if not valid_nodes:
            return None
            
        # Сортируем по рейтингу по убыванию
        valid_nodes.sort(key=lambda x: x["ano_rating"], reverse=True)
        
        return valid_nodes[0]