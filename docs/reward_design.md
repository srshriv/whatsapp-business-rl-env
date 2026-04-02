# Reward Design Spec

This document defines how the per-step reward is computed and how it relates to the trajectory-level graders. It is an internal spec for implementing the reward module.

## 1. Final outcome reward (episode-level)

<!-- How we reward conversion / penalize churn at the end of an episode -->
## 1. Final outcome reward (episode-level)

The **final outcome reward** is applied only on the **terminal step** of an episode (`done=True`). It reflects how good the *overall result* of the conversation is, independent of the detailed step-by-step shaping.

The key goals:

- Strong positive reward for **successful, healthy conversions**.
- Clear negative reward for **bad failures** (churn with high annoyance, broken obligations).
- Neutral or mildly positive reward for **respectful, non-conversion outcomes** when the user is not a real buyer.
- The magnitude of this reward should dominate any single-step shaping signal.

### 1.1 Outcomes

We use `final_outcome` from the last state:

- `"converted"` – user has agreed to buy.
- `"churned"` – user dropped out or stopped responding and env ends unsuccessfully.
- `"escalated"` – conversation is handed off to a human as the primary resolution.
- `"unresolved"` – env ended without clear conversion or explicit churn (e.g., timeout or soft close).

These outcomes are interpreted together with:

- `final_satisfaction ∈ [0, 1]`
- `final_annoyance ∈ [0, 1]`
- `total_cost_to_business ≥ 0`

### 1.2 Conceptual reward rules

At a high level:

- **Converted**
  - Base reward: **large positive**.
  - Adjust up if:
    - `final_satisfaction` is high.
    - `final_annoyance` is low.
    - `total_cost_to_business` is reasonable (no extreme discounts/escalations).
  - Adjust down if:
    - `final_annoyance` is high (spammy or unpleasant sale).
    - `total_cost_to_business` is very high (conversion not efficient).

- **Churned**
  - Base reward: **negative**.
  - More negative if:
    - `final_annoyance` is high.
    - There are many expired obligations.
  - Less negative if:
    - `final_satisfaction` is still moderate and annoyance low (e.g., user truly not a fit but handled politely).

- **Escalated**
  - Base reward: **medium positive or neutral** depending on task:
    - Escalation is good if:
      - `final_satisfaction` increases.
      - It avoids churn in complex scenarios.
    - However:
      - `total_cost_to_business` increases with each escalation and should reduce net reward.
  - In simpler tasks (like Task 1), unnecessary escalations should be penalized via cost and graders.

- **Unresolved**
  - Base reward: **neutral to slightly positive** if:
    - `final_satisfaction` is moderate to high.
    - `final_annoyance` is low.
    - Obligations are not badly violated.
  - More negative if:
    - The episode ends with low satisfaction or high annoyance.
    - Critical obligations expired.

### 1.3 Priority over step rewards

- The final outcome reward should be **an order of magnitude larger** than the typical per-step shaping.
- The agent should not be able to game the system by collecting small step rewards while consistently ending in bad terminal outcomes.


## 2. Step-level shaping components

<!-- Small, dense rewards that guide behaviour within an episode -->
## 2. Step-level shaping components

Step-level shaping provides **small, dense rewards** at each step to guide learning, without overpowering the final outcome reward. These components encourage good local behaviour: staying relevant, respecting the user, and managing obligations.

Shaping is applied on *every step*, based on:

- Current and next state (before/after).
- The agent’s action.
- The user event (reply / no_reply / objections / etc.).
- Whether the step completed an obligation, created spam, etc.

### 2.1 Engagement and progress

Purpose: reward useful back-and-forth that moves the conversation forward.

- Positive shaping when:
  - The user replies (not `no_reply`), and
  - The stage makes progress (e.g., inquiry → qualification, or more info collected).
- Typical effects:
  - Small **positive** reward per genuinely productive exchange.
- No (or minimal) reward for:
  - Steps where nothing changes (no reply, no stage movement).

### 2.2 Obligation hygiene

Purpose: encourage creating and fulfilling obligations responsibly.

- Positive shaping:
  - When an important obligation is **completed on time**:
    - Small to medium **positive** reward proportional to `importance`.
- Negative shaping:
  - When an obligation **expires**:
    - **Negative** reward proportional to `importance`.
- This shaping aligns with the state dynamics:
  - Completing obligations also improves trust/satisfaction.
  - Missing obligations hurts them and should hurt reward too.

### 2.3 Relevance and appropriateness

Purpose: reward actions that match the situation and penalize irrelevant or poorly timed actions.

- Positive shaping:
  - If the chosen action is **relevant** to:
    - The current `stage` (e.g., asking clarifying questions in inquiry, giving price in negotiation).
    - The inferred `intent` and recent user event (e.g., answering the exact question asked).
- Negative shaping:
  - If the action is clearly **irrelevant**:
    - Answering a different question.
    - Asking for info that was already provided.
    - Pushing for sale when the user just said `not_interested`.

This can be implemented via a small rule-based relevance classifier.

### 2.4 Spam and annoyance control

Purpose: discourage spamming or over-following when the user is not responsive or explicitly disinterested.

- Negative shaping:
  - When the agent sends messages while:
    - The user hasn’t replied for multiple steps (`no_reply` streak), and
    - `annoyance` is already high, or
    - The last user event was `not_interested`.
- Effects:
  - Small to medium **negative** reward per spammy action.
- No negative shaping for:
  - Well-timed follow-ups created from `delay_decision`.
  - Necessary reminders for obligations, as long as they are not excessive.

### 2.5 Cost shaping

Purpose: reflect business cost at the step level, aligned with `cost_to_business`.

- Discount-related shaping:
  - When the agent offers a discount:
    - Apply a **negative** shaping component proportional to the size of the discount.
- Escalation-related shaping:
  - When the agent escalates to human:
    - Apply a **negative** shaping component representing human cost.
- Long episode shaping (optional):
  - If `episode_length` exceeds a task-specific “comfortable” range:
    - Small **negative** per extra step.

These shaping penalties are small individually, but they accumulate and encourage efficient use of resources.

### 2.6 Summary

- Step-level shaping should:
  - Reward constructive engagement, obligation fulfillment, relevant actions.
  - Penalize spam, missed obligations, and excessive cost.
- But:
  - Shaping magnitudes must be **small** compared to the final outcome reward.
  - Long-term success (conversion + satisfaction + low annoyance + reasonable cost) remains the main driver.


## 3. Relative magnitudes and priorities

<!-- How big final outcome rewards are compared to shaping -->
## 3. Relative magnitudes and priorities

The reward function combines:

- A **final outcome reward** applied once at the terminal step.
- **Step-level shaping** applied on every step.

To keep learning focused on long-term success:

- The **final outcome reward must dominate**.
  - A single conversion or bad churn outcome should outweigh any one step’s shaping.
  - Rough heuristic: a typical final outcome reward should be at least **5–10×** larger than a typical per-step shaping component.
- Step-level shaping is **supporting**, not primary:
  - It should help the agent discover good behaviours (engaging, following up, not spamming).
  - It should not make it optimal to chase small step positives while consistently failing at the final outcome.

In practice (when implemented):

- Typical per-step shaping magnitudes:
  - On the order of ±0.01 to ±0.1.
- Typical final outcome magnitudes:
  - On the order of ±1.0 to ±5.0 (depending on the task and scaling choice).

Exact numbers will be tuned later, but this ratio must be preserved.
## 4. Intended function interface

<!-- Python signature and expected inputs/outputs for the reward function -->

## 4. Intended function interface

The reward computation will be implemented as a Python function used by the environment’s `step()` method.

### 4.1 Core interface

The environment will have access to:

- `state_before`: snapshot of latent `State` before applying the agent action and user event.
- `state_after`: snapshot of latent `State` after all updates for this step.
- `action`: the `Action` taken by the agent.
- `user_event`: the `UserEvent` generated by the simulator for this step.
- `done`: boolean indicating whether this step terminated the episode.

Intended interface:

```python
def compute_step_reward(
    state_before,
    state_after,
    action,
    user_event,
    done: bool,
) -> tuple[float, dict]:
    """
    Returns:
        total_reward: float
        components: dict[str, float]  # e.g. {
            "engagement": ...,
            "obligations": ...,
            "relevance": ...,
            "spam": ...,
            "cost": ...,
            "final_outcome": ...,
        }
    """
```

### 4.2 Behaviour

- On **non-terminal** steps (`done=False`):
  - `compute_step_reward` should:
    - Calculate and sum the step-level shaping components:
      - Engagement/progress.
      - Obligation hygiene.
      - Relevance.
      - Spam/annoyance.
      - Cost.
    - Return a relatively small `total_reward`.

- On the **terminal** step (`done=True`):
  - In addition to shaping, it should:
    - Compute the **final outcome reward** using:
      - `final_outcome` (from `state_after`).
      - `final_satisfaction`, `final_annoyance`.
      - `total_cost_to_business`.
    - Add this outcome term into the `components["final_outcome"]`.
    - Return a `total_reward` dominated by this outcome component.

The environment (`WhatsAppEnv`) will:

- Call `compute_step_reward(...)` inside `_compute_reward`.
- Use `total_reward` as the reward from `step()`.
- Include `components` in the `info` dict for analysis/debugging and for graders to inspect if needed.