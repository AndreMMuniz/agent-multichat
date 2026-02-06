# Graph Workflow - User Profile System

## Current Workflow (with Profile Management)

```
START
  ↓
manage_history (load conversation)
  ↓
check_user_profile (check if user exists, load profile)
  ↓
load_user_context (load long-term memory)
  ↓
classify_message (detect intent)
  ↓
generate_response (personalized with name if available)
  ↓
extract_user_info (extract name from conversation)
  ↓
save_user_profile (save name to database)
  ↓
detect_critical_action (check for keywords)
  ↓
  ├─ [requires_approval] → create_pending_action → [INTERRUPT] → execute_approved_action
  └─ [normal] → save_response
  ↓
save_response (save to database)
  ↓
summarize_conversation (generate summary if substantial)
  ↓
  ├─ [should_summarize] → save_user_context → END
  └─ [skip] → END
```

## Node Count: 13 nodes
## Max Path Length: ~13 steps (non-HITL) or ~14 steps (HITL)
## Recursion Limit: 25 (safe margin)

## Key Features:
1. **Profile Check** - First node checks if user exists
2. **Name Extraction** - Happens after every response
3. **Personalization** - Name used in generate_response if available
4. **First Contact Detection** - Agent asks for name on first interaction
