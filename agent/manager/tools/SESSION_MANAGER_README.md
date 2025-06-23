# Session Manager Tool

The Session Manager Tool is responsible for creating new user sessions and initializing states with default values for the health management system.

## Overview

This tool provides a structured approach to session management by:
- Creating unique session IDs
- Initializing comprehensive state structures
- Tracking user progress through the health management workflow
- Providing session update and retrieval capabilities

## Functions

### 1. `session_manager_tool()`

Creates a new session and initializes state with default values.

**Parameters:**
- `email_id` (str, required): User's email address for session identification
- `app_name` (str, optional): Application name (defaults to "HealthManagerAgent")
- `initial_data` (dict, optional): Additional data to merge with default state

**Returns:**
```json
{
  "status": "success",
  "session_id": "uuid-string",
  "app_name": "HealthManagerAgent",
  "email_id": "user@example.com",
  "created_at": "2024-01-01T12:00:00Z",
  "state": {
    // Complete state structure
  },
  "message": "Session created successfully for user@example.com"
}
```

### 2. `update_session_state()`

Updates an existing session's state with new data.

**Parameters:**
- `session_id` (str): The session ID to update
- `updates` (dict): Key-value pairs to update in the state

### 3. `get_session_info()`

Retrieves information about an existing session.

**Parameters:**
- `session_id` (str): The session ID to retrieve

## State Structure

The default state includes the following sections:

### Session Metadata
- `session_id`: Unique session identifier
- `email_id`: User's email address
- `app_name`: Application name
- `created_at`: Session creation timestamp
- `last_updated`: Last update timestamp

### User Onboarding Status
- `onboarding_complete`: Boolean flag
- `intake_complete`: Boolean flag
- `report_uploaded`: Boolean flag
- `analysis_complete`: Boolean flag

### User Profile
```json
{
  "name": null,
  "age": null,
  "gender": null,
  "location": null,
  "height": null,
  "weight": null,
  "known_conditions": [],
  "allergies": [],
  "medications": [],
  "diet": null,
  "smoking": null,
  "alcohol": null,
  "activity_level": null
}
```

### Health Report Data
```json
{
  "lab_name": null,
  "report_title": null,
  "profile_name": null,
  "collection_date": null,
  "collection_time": null,
  "reporting_date": null,
  "reporting_time": null,
  "test_results": [],
  "results_to_follow": []
}
```

### Analysis Results
```json
{
  "risk_assessment": null,
  "recommendations": null,
  "dietary_plan": null,
  "lifestyle_plan": null,
  "follow_up_actions": []
}
```

### Generated Documents
```json
{
  "pdf_roadmap_url": null,
  "pdf_created_at": null
}
```

### Session Flow Tracking
- `current_step`: Current step in the workflow
- `completed_steps`: Array of completed steps
- `next_recommended_action`: Recommended next action

### Error Tracking
- `errors`: Array of errors encountered
- `warnings`: Array of warnings

## Usage Examples

### Basic Session Creation
```python
from session_manager import session_manager_tool

# Create a new session
result = session_manager_tool(
    email_id="user@example.com",
    app_name="HealthManagerAgent"
)

session_id = result['session_id']
state = result['state']
```

### Session with Custom Initial Data
```python
# Create session with pre-filled user data
custom_data = {
    "user_profile": {
        "name": "John Doe",
        "location": "New York"
    },
    "current_step": "intake_started"
}

result = session_manager_tool(
    email_id="john.doe@example.com",
    initial_data=custom_data
)
```

### Updating Session State
```python
from session_manager import update_session_state

# Update user profile
updates = {
    "user_profile.name": "Jane Smith",
    "user_profile.age": "30",
    "current_step": "intake_complete",
    "completed_steps": ["session_created", "intake_started"]
}

update_result = update_session_state(session_id, updates)
```

## Integration with ADK

To integrate this tool with your ADK agents:

1. **Import the tool:**
```python
from tools.session_manager import session_manager_tool
```

2. **Add to agent tools list:**
```python
agent = Agent(
    name="your_agent",
    tools=[session_manager_tool, other_tools...]
)
```

3. **Use in agent instructions:**
```python
instruction="""
When a new user starts, use the session_manager_tool to create a session:
- Call session_manager_tool with the user's email
- Store the session_id for future reference
- Use the returned state structure to track progress
"""
```

## Testing

Run the test script to verify functionality:

```bash
cd agent/manager/tools
python test_session_manager.py
```

## Future Enhancements

- Integration with actual session service (DatabaseSessionService)
- Persistent state storage
- Session expiration handling
- Multi-user session management
- Real-time state synchronization 