# Sense API Design Documentation

This document explains the core concepts and design decisions for the Sense API endpoints.

---

## Core Concepts

### 1. Timeline (`/api/timeline`)

**What it is:** Raw chronological stream of app usage events.

**Definition:** Each event represents continuous usage of a single app with:
- Start time
- End time
- Duration
- App identifier (bundle_id or web domain)

**Use case:**
- "What apps did I use today?"
- "Show me everything I did between 2-4pm"
- Basic activity log for verification/debugging

**Example:**
```
09:00-09:15  IntelliJ (15 min)
09:15-09:16  Slack (1 min)
09:16-09:30  IntelliJ (14 min)
09:30-10:00  Chrome (30 min)
```

**Design decisions:**
- Simple passthrough of KnowledgeC data
- No aggregation or analysis
- Supports filtering by app, date range, pagination
- System apps excluded by default

---

### 2. Context Switches (`/api/switches`)

**What it is:** Transitions between different apps.

**Definition:** A context switch occurs when you move from App A to App B:
```
Event 1: IntelliJ  09:00-09:15
Event 2: Slack     09:16-09:20
         ↑ Context switch at 09:16 (gap: 1 min)
```

**Key metrics:**
- `from_app`: Previous app
- `to_app`: Next app
- `time`: When the switch occurred
- `gap_seconds`: Idle time between apps (can be negative for overlaps)

**Use case:**
- "How often am I switching apps?"
- "What's my most common app pair?" (e.g., IntelliJ ↔ Chrome)
- "Am I multitasking too much?"

**Design decisions:**
- Calculated from consecutive timeline events
- Optional `min_gap_seconds` filter to ignore instant switches
- Counts every transition (A→B, B→A are two separate switches)
- Max 7-day range to prevent performance issues

---

### 3. Focus Sessions (`/api/focus`)

**What it is:** Periods of sustained work in a single app.

**Definition:** A focus session groups consecutive events of the same app, split when there's a gap > threshold:

```
09:00-09:15  IntelliJ
09:16-09:30  IntelliJ  (gap: 1 min → same session)
09:40-10:00  IntelliJ  (gap: 10 min → new session)

Result:
- Session 1: 09:00-09:30 (29 min, 2 events)
- Session 2: 09:40-10:00 (20 min, 1 event)
```

**Key metrics (per app):**
- `total_time_minutes`: Sum of all session durations
- `total_sessions`: Number of distinct focus sessions
- `avg_session_minutes`: Average session length
- `longest_session_minutes`: Longest unbroken session
- `focus_sessions[]`: Array of individual sessions with start/end/duration

**Use case:**
- "How long was my longest coding session today?"
- "Show me all my deep work periods for the week"
- Timeline visualization of focused work
- Identify productivity patterns

**Design decisions:**
- **Session gap threshold:** 5 minutes (Pomodoro-aligned)
  - Rationale: Short breaks (coffee, bathroom) shouldn't break sessions
  - Configurable in `config.py` for future user customization
- Sessions sorted DESC by start time (newest first)
- No merging on backend—frontend can merge <5min gaps for display
- Groups by `bundle_id` (not display name) for accuracy
- Excludes system apps by default

**Why 5 minutes?**
- Standard Pomodoro break: 5 minutes
- Quick interruptions (Slack check, email glance) are <5min
- Longer gaps indicate genuine context switches

---

### 4. Interruptions (`/api/interruptions`)

**What it is:** Brief distractions that break your focus flow.

**Definition:** An interruption is a specific pattern where:
1. You're working in App A
2. Briefly switch to App B (< threshold duration)
3. Return to App A

```
09:00-09:15  IntelliJ
09:15-09:16  Slack      (1 min interruption)
09:16-09:30  IntelliJ   ← Resumed work

Pattern: A → B (brief) → A
```

**Criteria (both must be true):**
- **Option A:** Middle app duration ≤ `max_interruption_seconds` (default: 300s = 5 min)
- **Option B:** User returns to the original app (A → B → A pattern)

**Key metrics:**
- `interrupted_app`: What you were working on (App A)
- `interrupting_app`: What distracted you (App B)
- `time`: When the interruption occurred
- `duration_seconds`: How long the distraction lasted
- `gap_before_seconds`: Idle time before interruption
- `gap_after_seconds`: Idle time before resuming work

**Aggregate metrics:**
- Total interruptions
- Most interrupting apps (Slack, Mail, etc.)
- Most interrupted apps (IntelliJ, Figma—your focus work)
- Average interruption duration

**Use case:**
- "What apps distract me most?"
- "How often do I get interrupted while coding?"
- "Is Slack breaking my flow?"
- Identify and block notification sources

**Design decisions:**
- **Max interruption duration:** 5 minutes (default: 300 seconds)
  - Rationale: Aligns with focus session gap threshold
  - Quick checks: <1 min (Slack message, email)
  - Brief tasks: 2-3 min (respond to message, check calendar)
  - 5+ min = intentional work, not interruption
  - Configurable in `config.py`
- Requires return to original app (strict A→B→A pattern)
- Tracks both roles: interrupted vs interrupting
- Summary stats for top interrupters/interrupted apps

**Why 5 minutes?**
- Consistency with focus session threshold
- Covers 90%+ of notification-driven behavior
- Anything longer suggests deliberate task switching
- If you spend 10 minutes in Slack, that's work, not distraction

**What's NOT an interruption:**
```
IntelliJ → Slack (10 min) → IntelliJ    # Too long (10 min > 5 min)
IntelliJ → Slack → Chrome                # Didn't return to IntelliJ
IntelliJ → IntelliJ                      # No interruption
```

---

## API Comparison Table

| Concept | Endpoint | Calculates | Groups By | Key Metric | Use Case |
|---------|----------|------------|-----------|------------|----------|
| **Timeline** | `/api/timeline` | Nothing (raw events) | None | Event list | "What did I do?" |
| **Context Switches** | `/api/switches` | Transitions | Event pairs | Switch count | "Am I multitasking?" |
| **Focus Sessions** | `/api/focus` | Sustained work | Same app | Session duration | "When was I deep working?" |
| **Interruptions** | `/api/interruptions` | Flow breaks | A→B→A pattern | Interruption count | "What distracts me?" |

---

## Common Design Patterns

All APIs share:
- **Date range validation:** Max 7 days to prevent performance issues
- **Pagination:** Supports `page` and `limit` parameters
- **Sorting:** Configurable `order` (asc/desc)
- **System app filtering:** Excludes macOS system apps by default
- **Caching:** In-memory cache with TTL (60 seconds)
- **Error handling:** 400 for validation, 404 for no data

---

## Configuration Parameters

Defined in `src/sense/config.py`:

```python
# Focus sessions
focus_session_gap_minutes: float = 5.0

# Interruptions
max_interruption_seconds: int = 300  # 5 minutes
```

These will be user-configurable in future versions.

---

## Future Enhancements

- **Daily breakdowns:** Group metrics by day/hour
- **Productivity scores:** Rate focus quality
- **Recommendations:** "You're most focused 9-11am"
- **Alerts:** "Slack interrupted you 40 times today"
- **Trends:** Week-over-week comparison
