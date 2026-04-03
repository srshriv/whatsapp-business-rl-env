# Environment Design Rationale

## Why Long-Horizon, Multi-Route Conversations?

Traditional chatbots work on short, predictable flows. Real WhatsApp Business conversations are:

- **Long**: 5-20+ exchanges, with delays and follow-ups.
- **Multi-route**: 
  - Fast conversions (impulsive users).
  - Ghosting/churn (busy users).
  - Objection handling (price-sensitive).
  - Delayed decisions with follow-ups.
  - Escalations to humans.

The environment forces agents to learn **all routes**, not just the happy path.

## Why Obligations and Time Pressure?

Real conversations create **memory**:

- User says "remind me tomorrow" → obligation.
- Agent promises "I'll send you a quote" → obligation.
- If ignored → trust/satisfaction drop, annoyance rises.

**Time matters**:
- Patience decays each step.
- Obligations have `due_at` timestamps.
- Expired obligations hurt metrics and reward.

This creates **delayed rewards** and **planning challenges** that simple chatbots don't face.

## Why Trajectory-Centric Evaluation?

Per-message rewards are noisy and encourage spam. Instead:

- **Graders** (`grade_task1/2/3`) score entire conversations.
- **Reward** is mostly final outcome, with small step shaping.
- **Metrics** focus on business outcomes:
  - Conversion rate.
  - Satisfaction/annoyance.
  - Obligation hygiene.
  - Cost efficiency.

This aligns with real business goals: **healthy conversions at reasonable cost**.

## Why Multi-Objective?

Pure conversion-maximizing agents would:
- Spam every user.
- Give huge discounts.
- Escalate everything.

We balance:
- Conversion vs satisfaction vs annoyance vs cost.
- Short-term wins vs relationship-building.
- Automation vs human handoff.

## Task Progression

**Task 1**: Learn basic inquiry handling.
**Task 2**: Learn multi-step sales.
**Task 3**: Learn robust adaptation to user variability.

Each builds on the previous, with increasing complexity.