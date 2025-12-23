"""Deterministic rule evaluator executor (A4).

Strict, side-effect free implementation following P3+ contract.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.action_contracts import ActionRequest
from app.executors.base import ExecutorLimits


class RuleEvaluatorV1:
    """Evaluate simple deterministic rules against an input dict.

    - executor_id: "rule_evaluator_v1"
    - version: "1.0.0"
    - capabilities: []
    - behavior: strict schema validation; raises ValueError("INVALID_PAYLOAD") on invalid payload
    """

    def __init__(self):
        self.executor_id = "rule_evaluator_v1"
        self.version = "1.0.0"
        self.capabilities: list[str] = []
        self.limits = ExecutorLimits(
            timeout_ms=1000,
            max_payload_bytes=10_000,
            max_depth=10,
            max_list_items=100,
        )

    def _validate_schema(self, payload: Dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            raise ValueError("INVALID_PAYLOAD")

        rules = payload.get("rules")
        input_obj = payload.get("input")

        if not isinstance(rules, list) or len(rules) == 0:
            raise ValueError("INVALID_PAYLOAD")
        if not isinstance(input_obj, dict):
            raise ValueError("INVALID_PAYLOAD")

        allowed_ops = {"==", "!=", ">", ">=", "<", "<="}

        for r in rules:
            if not isinstance(r, dict):
                raise ValueError("INVALID_PAYLOAD")
            if set(r.keys()) != {"field", "op", "value"}:
                raise ValueError("INVALID_PAYLOAD")
            field = r.get("field")
            op = r.get("op")
            value = r.get("value")

            if not isinstance(field, str) or not isinstance(op, str):
                raise ValueError("INVALID_PAYLOAD")
            if op not in allowed_ops:
                raise ValueError("INVALID_PAYLOAD")
            if field not in input_obj:
                raise ValueError("INVALID_PAYLOAD")

            # Strict type checking: no coercion
            input_val = input_obj[field]
            # For comparison operators other than equality, require numeric types
            if op in {">", ">=", "<", "<="}:
                if not isinstance(input_val, (int, float)) or not isinstance(value, (int, float)):
                    raise ValueError("INVALID_PAYLOAD")
            else:
                # For == and != require same type
                if type(input_val) is not type(value):
                    raise ValueError("INVALID_PAYLOAD")

    def _evaluate_rule(self, rule: Dict[str, Any], input_obj: Dict[str, Any]) -> bool:
        field = rule["field"]
        op = rule["op"]
        value = rule["value"]
        input_val = input_obj[field]

        if op == "==":
            return input_val == value
        if op == "!=":
            return input_val != value
        if op == ">":
            return input_val > value
        if op == ">=":
            return input_val >= value
        if op == "<":
            return input_val < value
        if op == "<=":
            return input_val <= value

        # Should not reach here due to validation
        return False

    def execute(self, req: ActionRequest) -> Any:
        # Validate payload strictly; raises ValueError("INVALID_PAYLOAD") on any problem
        payload = req.payload
        try:
            self._validate_schema(payload)
        except ValueError:
            # Per governance decision: invalid payload => raise ValueError to be mapped to FAILED
            raise

        rules: List[Dict[str, Any]] = payload["rules"]
        input_obj: Dict[str, Any] = payload["input"]

        matches: List[Dict[str, Any]] = []
        for r in rules:
            if self._evaluate_rule(r, input_obj):
                # Keep rule dict as-is (deterministic ordering assumed from input list)
                matches.append(r)

        result = {"matched": bool(matches), "matches": matches}
        return result
