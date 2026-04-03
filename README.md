# WhatsApp Business RL Environment

A reinforcement learning environment for training WhatsApp Business chat agents to handle sales/support conversations with realistic user behavior, obligations, and multi-objective evaluation.

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Run evaluation (once Dev C finishes)
python -m evaluation.run_agent --agent random --task task1 --episodes 100
```

## Environment Overview

The environment simulates **long-horizon WhatsApp conversations** between a business agent and users with different personalities and intents.

### Key Features

- **Multi-route conversations**: fast conversions, ghosting, objections, follow-ups, escalations.
- **Obligations**: track promises ("I'll send you a quote") and user requests ("remind me later").
- **Time pressure**: patience decays, obligations expire if ignored.
- **Trajectory-first evaluation**: reward and graders focus on full conversation outcomes.
- **Multi-objective**: balance conversion, satisfaction, annoyance, and cost.

## Action Space

The agent chooses from these `ActionType`s:

| Action | Description |
|--------|-------------|
| `PROVIDE_INFO` | Answer questions, give product details |
| `ASK_CLARIFICATION` | Ask for missing info (budget, specs, timing) |
| `FOLLOW_UP` | Remind about pending obligations or delayed decisions |
| `OFFER_DISCOUNT` | Negotiate price |
| `ESCALATE_HUMAN` | Hand off to human support |
| `WAIT` | Don't send a message this step |

### Action Constraints

- **Rate limits**: Can't spam; `annoyance` increases if too frequent.
- **Obligation-driven**: `FOLLOW_UP` is stronger when obligations are due.
- **Stage-aware**: `ASK_CLARIFICATION` is more effective early, `OFFER_DISCOUNT` in negotiation.

## Observation Space

Agent sees:

| Field | Type | Notes |
|-------|------|-------|
| `chat_history` | `List[str]` | Full message log |
| `stage` | `StageType` | `inquiry`, `qualification`, `negotiation`, `closing`, `post_sale` |
| `intent` | `IntentType` | Inferred from stage (not true user intent) |
| `sentiment` | `float [-1, 1]` | Derived from satisfaction |
| `uncertainties` | `List[str]` | Text flags when trust/patience low |
| `obligations` | `ObligationSummary` | All open/pending obligations |
| `step_count` | `int` | Current time step |

### Observation Noise

- `intent`: Noisy inference, not true user intent.
- `sentiment`: Derived from satisfaction, not raw values.
- `uncertainties`: Threshold-based text flags (e.g., "patience low").

Agent must infer true state from behavior and context.

## Hidden State (Environment Internal)

| Variable | Range | Meaning |
|----------|-------|---------|
| `trust` | [0,1] | User belief in business reliability |
| `patience` | [0,1] | Tolerance for delays/extra messages |
| `annoyance` | [0,1] | User irritation level |
| `satisfaction` | [0,1] | Overall conversation satisfaction |
| `conversion_prob` | [0,1] | Likelihood user will buy |
| `cost_to_business` | ≥0 | Cumulative cost (discounts, escalations) |

See `docs/state_semantics.md` for full dynamics.

## Tasks

| Task | Max Steps | Focus | User Mix |
|------|-----------|-------|----------|
| `task1` | 8 | Simple inquiry | Balanced |
| `task2` | 12 | Multi-step sales | Price-sensitive heavy |
| `task3` | 16 | Dynamic users | Mixed, challenging |

See `tasks/configs.py` for full settings.

## Evaluation

**Trajectory-first metrics** (`tasks.metrics.extract_trajectory_stats`):

| Metric | Type |
|--------|------|
| `final_outcome` | converted/churned/escalated/unresolved |
| `final_satisfaction` | [0,1] |
| `final_annoyance` | [0,1] |
| `num_obligations_created` | int |
| `num_obligations_completed` | int |
| `num_obligations_expired` | int |
| `num_escalations` | int |
| `total_cost_to_business` | ≥0 |
| `episode_length` | int |

**Task-specific graders** (`tasks.graders.grade_taskX`):

- `task1`: inquiry resolution + satisfaction + short length
- `task2`: sales flow + info collection + negotiation
- `task3`: robustness across users + obligation handling

## Reward Structure

`reward/core.py` computes:

**Step-level shaping** (small):
- Engagement (progress)
- Obligation hygiene
- Spam penalties
- Cost penalties

**Final outcome** (large):
- Big bonus for healthy conversions
- Penalty for churn
- Balanced for escalations

See `docs/reward_design.md` for details.

## Development Structure

## Detailed Design

See `docs/`:
- `state_semantics.md`: state dynamics
- `trajectory_metrics_and_graders.md`: graders
- `reward_design.md`: reward breakdown
- `design.md`: rationale