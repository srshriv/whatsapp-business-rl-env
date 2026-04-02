from typing import Dict, Any, Tuple


def compute_step_reward(
    state_before: Dict[str, Any],
    state_after: Dict[str, Any],
    action,
    user_event: str,
    done: bool,
) -> Tuple[float, Dict[str, float]]:
    """
    Compute total reward and components for one step.

    state_before/state_after: snapshots of State (dicts or objects converted to dicts).
    action: Action object.
    user_event: string label from USER_EVENTS.
    done: whether this step terminated the episode.
    """
    components: Dict[str, float] = {
        "engagement": 0.0,
        "obligations": 0.0,
        "relevance": 0.0,
        "spam": 0.0,
        "cost": 0.0,
        "final_outcome": 0.0,
    }

    # --- Engagement: reward user replies + stage progress ---
    if user_event != "no_reply":
        if state_after.get("stage") != state_before.get("stage"):
            components["engagement"] += 0.05

    # --- Obligations: placeholder, to be updated once obligation_events are surfaced ---
    # For now, keep 0.0; Dev A can later add calls here using info.

    # --- Relevance: placeholder; can be improved once you have ActionType and Observation ---
    # For now, components["relevance"] = 0.0

    # --- Spam / annoyance penalty ---
    annoyance_after = state_after.get("annoyance", 0.0)
    action_type = getattr(action, "action_type", None)
    if action_type not in ("WAIT",) and annoyance_after > 0.7 and user_event == "no_reply":
        components["spam"] -= 0.05

    # --- Cost penalty ---
    cost_before = state_before.get("cost_to_business", 0.0)
    cost_after = state_after.get("cost_to_business", 0.0)
    delta_cost = max(0.0, cost_after - cost_before)
    if delta_cost > 0:
        components["cost"] -= delta_cost

    total_reward = sum(components.values())

    # --- Final outcome reward on terminal step ---
    if done:
        outcome = state_after.get("outcome", "unresolved")
        final_satisfaction = state_after.get("satisfaction", 0.0)
        final_annoyance = state_after.get("annoyance", 0.0)
        total_cost = state_after.get("cost_to_business", 0.0)

        outcome_bonus = 0.0
        if outcome == "converted":
            outcome_bonus = 3.0 * final_satisfaction - 1.5 * final_annoyance - 0.5 * total_cost
        elif outcome == "churned":
            outcome_bonus = -2.0 - final_annoyance
        elif outcome == "escalated":
            outcome_bonus = 1.0 * final_satisfaction - 0.5 * total_cost
        else:  # unresolved
            outcome_bonus = 0.5 * final_satisfaction - final_annoyance

        components["final_outcome"] = outcome_bonus
        total_reward += outcome_bonus

    return float(total_reward), components