from typing import List, Dict, Any, Tuple

# trajectory: list of (obs, action, reward, info)
def extract_trajectory_stats(trajectory: List[Tuple[Any, Any, float, Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Extracts core trajectory-level statistics used by all graders.
    """
    episode_length = len(trajectory)
    if episode_length == 0:
        return {
            "final_outcome": "unresolved",
            "final_satisfaction": 0.0,
            "final_annoyance": 0.0,
            "num_obligations_created": 0,
            "num_obligations_completed": 0,
            "num_obligations_expired": 0,
            "num_escalations": 0,
            "total_cost_to_business": 0.0,
            "episode_length": 0,
        }

    # last transition
    last_obs, last_action, last_reward, last_info = trajectory[-1]

    # assume env puts a state snapshot into info
    state_snapshot = last_info.get("state_snapshot", {})
    final_outcome = state_snapshot.get("outcome", last_info.get("outcome", "unresolved"))
    final_satisfaction = state_snapshot.get("satisfaction", 0.0)
    final_annoyance = state_snapshot.get("annoyance", 0.0)
    total_cost_to_business = state_snapshot.get("cost_to_business", 0.0)

    num_escalations = 0
    num_obligations_created = 0
    num_obligations_completed = 0
    num_obligations_expired = 0

    for obs, action, reward, info in trajectory:
        # count escalations by action_type if available
        try:
            if getattr(action, "action_type", None) == "ESCALATE_HUMAN":
                num_escalations += 1
        except Exception:
            pass

        # assume env logs obligation events in info, e.g. info["obligation_events"] = [{"type": "created"}, ...]
        for ev in info.get("obligation_events", []):
            ev_type = ev.get("type")
            if ev_type == "created":
                num_obligations_created += 1
            elif ev_type == "completed":
                num_obligations_completed += 1
            elif ev_type == "expired":
                num_obligations_expired += 1

    return {
        "final_outcome": final_outcome,
        "final_satisfaction": float(final_satisfaction),
        "final_annoyance": float(final_annoyance),
        "num_obligations_created": int(num_obligations_created),
        "num_obligations_completed": int(num_obligations_completed),
        "num_obligations_expired": int(num_obligations_expired),
        "num_escalations": int(num_escalations),
        "total_cost_to_business": float(total_cost_to_business),
        "episode_length": int(episode_length),
    }