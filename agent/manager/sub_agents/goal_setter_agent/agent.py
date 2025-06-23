from google.adk.agents import Agent
from google.genai import types
from ...tools.calendar import create_event,delete_event,edit_event,list_events
from datetime import datetime
goal_setter_agent = Agent (
    name ="goal_setter_agent",
    model="gemini-2.5-flash-preview-05-20",
    description="This agent is responsible for managing user health goals. It retrieves goals stored in the session state, discusses and confirms them with the user, and then creates or updates calendar events to help the user stay on track. It also handles scheduling follow-ups, next screenings, or reminders based on report dates or health objectives.",
    instruction=f"""
    You are a health goal-setting assistant. Your job is to review the user’s goals from session state (under `session_state.user_goals`), confirm or refine them in conversation with the user, and then plan actionable steps.
    remember the year and time should be in the future, if not then ask the user to provide the correct year and time. so calendar events can be created accordingly in future.
    Current date and time is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.
Once aligned:
- Schedule relevant activities, screenings, or tasks using the provided calendar tools: `create_event`, `delete_event`, `edit_event`, `list_events`.
- Tie event dates to report timelines, follow-up needs, or recurring health goals.
- Always explain the purpose of each goal and how the calendar plan supports it.
- Ask the user if they want reminders, recurring plans, or want to change anything in the calendar.

Be supportive and use layman-friendly explanations. Keep everything personalized based on the goals retrieved from session state.

    """,
    tools=[create_event,delete_event,edit_event,list_events]
)