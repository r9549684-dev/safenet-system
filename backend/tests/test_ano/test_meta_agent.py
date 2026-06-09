"""Тесты для SafeNet ANO — Meta-Agent + Shadow Mode."""

import pytest

from app.services.ano.causality_engine import Incident
from app.services.ano.decision_memory import DecisionMemory
from app.services.ano.meta_agent import MetaAgent, ShadowAction


class TestMetaAgent:
    @pytest.fixture
    def memory(self) -> DecisionMemory:
        return DecisionMemory()

    @pytest.fixture
    def agent(self, memory: DecisionMemory) -> MetaAgent:
        return MetaAgent(memory=memory, shadow_mode=True)

    def test_evaluate_proposal_shadow_mode(self, agent: MetaAgent, memory: DecisionMemory) -> None:
        context = {"geo": "UAE", "protocol": "VLESS"}
        action_id = agent.evaluate_proposal(
            context=context,
            proposed_action="switch_to_WireGuard",
            predicted_downtime=0.5,
        )
        
        # Проверка лога
        log = agent.get_shadow_log()
        assert len(log) == 1
        assert log[0].proposed_action == "switch_to_WireGuard"
        assert log[0].executed is False
        assert log[0].action_id == action_id

        # Проверка записи в память
        assert len(memory._entries) == 1
        entry = list(memory._entries.values())[0]
        assert entry.action_taken == "SHADOW:switch_to_WireGuard"

    def test_analyze_incidents_empty(self, agent: MetaAgent) -> None:
        report = agent.analyze_incidents([])
        assert "No incidents to analyze" in report

    def test_analyze_incidents_patterns(self, agent: MetaAgent) -> None:
        incidents = [
            Incident(
                id="1", 
                scope="datacenter", 
                confidence=0.8,
                affected_entities=["srv-1", "srv-2"], 
                root_cause="overload",
                resolution="none", 
                evidence={}, 
                hypotheses=[]
            ),
            Incident(
                id="2", 
                scope="datacenter", 
                confidence=0.9,
                affected_entities=["srv-3"], 
                root_cause="overload",
                resolution="none", 
                evidence={}, 
                hypotheses=[]
            ),
            Incident(
                id="3", 
                scope="server", 
                confidence=0.7,
                affected_entities=["srv-4"], 
                root_cause="vm_failure",
                resolution="handover", 
                evidence={}, 
                hypotheses=[]
            ),
        ]
        report = agent.analyze_incidents(incidents)
        
        assert "Total incidents analyzed: 3" in report
        assert "Most frequent scope: datacenter (2 cases)" in report
        assert "Most frequent root cause: overload (2 cases)" in report
        assert "Shadow Mode Status: ACTIVE" in report

    def test_shadow_mode_toggle(self, memory: DecisionMemory) -> None:
        # Тест выключенного Shadow Mode (действия не пишутся в память как SHADOW)
        agent_inactive = MetaAgent(memory=memory, shadow_mode=False)
        agent_inactive.evaluate_proposal(
            context={"geo": "IR"},
            proposed_action="enable_fallback",
        )
        
        # В память не должно быть записано действие с префиксом SHADOW:
        shadow_entries = [
            e for e in memory._entries.values() 
            if e.action_taken.startswith("SHADOW:")
        ]
        assert len(shadow_entries) == 0
        
        # Но лог теневых действий всё равно ведётся для аудита
        assert len(agent_inactive.get_shadow_log()) == 1
        assert agent_inactive.get_shadow_log()[0].proposed_action == "enable_fallback"

    def test_shadow_action_dataclass(self) -> None:
        action = ShadowAction(
            action_id="test-123",
            timestamp=1700000000.0,
            context={"geo": "UAE"},
            proposed_action="switch_protocol",
            predicted_downtime=1.5,
            executed=False,
        )
        assert action.action_id == "test-123"
        assert action.executed is False
        assert action.predicted_downtime == 1.5
