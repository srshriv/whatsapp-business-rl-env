from typing import List, Any, Dict, Tuple
from .metrics import extract_trajectory_stats


def _outcome_base_score(outcome: str) -> float:
    if outcome == "converted":
        return 1.0
    if outcome == "churned":
        return 0.0
    if outcome == "escalated":
        return 0.6
    # unresolved or anything else
    return 0.4


def grade_task1(trajectory: List[Tuple[Any, Any, float, Dict[str, Any]]]) -> float:
    stats = extract_trajectory_stats(trajectory)

    outcome_score = _outcome_base_score(stats["final_outcome"])
    sat = stats["final_satisfaction"]
    ann = stats["final_annoyance"]
    length = stats["episode_length"]
    expired = stats["num_obligations_expired"]

    # Normalize episode length: ideal <= 10 steps
    length_penalty = max(0.0, (length - 10) / 10.0)
    length_term = max(0.0, 1.0 - length_penalty)

    obligations_term = max(0.0, 1.0 - 0.2 * expired)

    score = (
        0.4 * outcome_score +
        0.3 * sat +
        0.2 * (1.0 - ann) +
        0.05 * length_term +
        0.05 * obligations_term
    )
    return max(0.0, min(1.0, score))


def grade_task2(trajectory: List[Tuple[Any, Any, float, Dict[str, Any]]]) -> float:
    stats = extract_trajectory_stats(trajectory)

    outcome_score = _outcome_base_score(stats["final_outcome"])
    sat = stats["final_satisfaction"]
    ann = stats["final_annoyance"]
    expired = stats["num_obligations_expired"]
    cost = stats["total_cost_to_business"]

    obligations_term = max(0.0, 1.0 - 0.1 * expired)
    cost_term = 1.0 / (1.0 + cost)

    score = (
        0.45 * outcome_score +
        0.25 * sat +
        0.15 * (1.0 - ann) +
        0.10 * obligations_term +
        0.05 * cost_term
    )
    return max(0.0, min(1.0, score))


def grade_task3(trajectory: List[Tuple[Any, Any, float, Dict[str, Any]]]) -> float:
    stats = extract_trajectory_stats(trajectory)

    outcome_score = _outcome_base_score(stats["final_outcome"])
    sat = stats["final_satisfaction"]
    ann = stats["final_annoyance"]
    expired = stats["num_obligations_expired"]
    cost = stats["total_cost_to_business"]
    escalations = stats["num_escalations"]

    obligations_term = max(0.0, 1.0 - 0.15 * expired)
    cost_term = 1.0 / (1.0 + cost)
    esc_penalty = max(0.0, (escalations - 3) / 5.0)
    esc_term = max(0.0, 1.0 - esc_penalty)

    score = (
        0.35 * outcome_score +
        0.25 * sat +
        0.15 * (1.0 - ann) +
        0.10 * obligations_term +
        0.10 * cost_term +
        0.05 * esc_term
    )
    return max(0.0, min(1.0, score))