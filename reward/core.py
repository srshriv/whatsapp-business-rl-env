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
    state_before/state_after can be actual State objects or dict snapshots
    (Dev A can adapt the call).
    """
    components: Dict[str, float] = {
        "engagement": 0.0,
        "obligations": 0.0,
        "relevance": 0.0,
        "spam": 0.0,
        "cost": 0.0,
        "final_outcome": 0.0,
    }

    # --- Engagement: reward when user replies and stage progresses ---
    if user_event != "no_reply":
        # simple heuristic: if stage changed, count as progress
        if state_after.get("stage") != state_before.get("stage"):
            components["engagement"] += 0.05

    # --- Obligations: expect Dev A to mark obligation_events in info; here we just use state diffs if needed ---
    # Placeholder: leave at 0, to be enriched once you know how obligation events are surfaced.

    # --- Relevance: placeholder (can be improved later) ---
    # For now, leave 0 or add simple rules once you see ActionType and Observation.

    # --- Spam / annoyance: penalize sending messages when annoyance already high ---
    annoyance_after = state_after.get("annoyance", 0.0)
    if getattr(action, "action_type", None) not in ("WAIT",) and annoyance_after > 0.7 and user_event == "no_reply":
        components["spam"] -= 0.05

    # --- Cost: discount + escalation ---
    cost_before = state_before.get("cost_to_business", 0.0)
    cost_after = state_after.get("cost_to_business", 0.0)
    delta_cost = max(0.0, cost_after - cost_before)
    if delta_cost > 0:
        components["cost"] -= delta_cost  # negative, proportional to cost

    total_reward = sum(components.values())

    # --- Final outcome reward on terminal step ---
    if done:
        outcome = state_after.get("outcome", "unresolved")
        final_satisfaction = state_after.get("satisfaction", 0.0)
        final_annoyance = state_after.get("annoyance", 0.0)
        total_cost = state_after.get("cost_to_business", 0.0)

        outcome_bonus = 0.0
        if outcome == "converted":
            outcome_bonus = 3.0 * final_satisfaction - 1.5 * final_annoyance
            outcome_bonus -= 0.5 * total_cost
        elif outcome == "churned":
            outcome_bonus = -2.0 - final_annoyance
        elif outcome == "escalated":
            outcome_bonus = 1.0 * final_satisfaction - 0.5 * total_cost
        else:  # unresolved
            outcome_bonus = 0.5 * final_satisfaction - final_annoyance

        components["final_outcome"] = outcome_bonus
        total_reward += outcome_bonus

    return float(total_reward), components
    