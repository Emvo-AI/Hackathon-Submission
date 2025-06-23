# ───────────────────────────────────────────────────────────────
# SessionManagerTool – Google-ADK functional tool
# Creates new sessions and initializes states with default values
# ───────────────────────────────────────────────────────────────
# This tool is responsible for creating new user sessions and setting up
# initial state with default values for the health management system.
# ───────────────────────────────────────────────────────────────

from __future__ import annotations
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

# ───────────────────────── schema ──────────────────────────────
class SessionArgs(BaseModel):
    """Arguments required by SessionManagerTool."""
    email_id: str = Field(
        description="User's email address to identify the session."
    )
    app_name: str = Field(
        default="HealthManagerAgent",
        description="Application name for the session."
    )
    initial_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional initial data to include in the session state."
    )


def session_manager_tool(
    email_id: str,
    app_name: str = "HealthManagerAgent",
    initial_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Creates a new session and initializes state with default values for health management.
    
    This tool sets up the foundational state structure that other agents will use
    throughout the user's health management journey.
    
    Args:
        email_id: str -> User's email address (required for session identification)
        app_name: str -> Application name (defaults to "HealthManagerAgent")
        initial_data: Optional[Dict] -> Any additional initial data to include
    
    Returns:
        Dict containing session information and initialized state structure
    """
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    
    # Default state structure for health management
    default_state = {
        # Session metadata
        "session_id": session_id,
        "email_id": email_id,
        "app_name": app_name,
        "created_at": created_at,
        "last_updated": created_at,
        
        # User onboarding status
        "onboarding_complete": False,
        "intake_complete": False,
        "report_uploaded": False,
        "analysis_complete": False,
        
        # User profile (to be filled during intake)
        "user_profile": {
            "name": None,
            "age": None,
            "gender": None,
            "location": None,
            "height": None,
            "weight": None,
            "known_conditions": [],
            "allergies": [],
            "medications": [],
            "diet": None,
            "smoking": None,
            "alcohol": None,
            "activity_level": None
        },
        
        # Health report data (to be filled after report upload)
        "health_report": {
            "lab_name": None,
            "report_title": None,
            "profile_name": None,
            "collection_date": None,
            "collection_time": None,
            "reporting_date": None,
            "reporting_time": None,
            "test_results": [],
            "results_to_follow": []
        },
        
        # Analysis results (to be filled after analysis)
        "analysis_results": {
            "risk_assessment": None,
            "recommendations": None,
            "dietary_plan": None,
            "lifestyle_plan": None,
            "follow_up_actions": []
        },
        
        # Generated documents
        "generated_documents": {
            "pdf_roadmap_url": None,
            "pdf_created_at": None
        },
        
        # Session flow tracking
        "current_step": "session_created",
        "completed_steps": [],
        "next_recommended_action": "complete_intake",
        
        # Error tracking
        "errors": [],
        "warnings": []
    }
    
    # Merge with any provided initial data
    if initial_data:
        default_state.update(initial_data)
    
    # Create session response
    session_info = {
        "status": "success",
        "session_id": session_id,
        "app_name": app_name,
        "email_id": email_id,
        "created_at": created_at,
        "state": default_state,
        "message": f"Session created successfully for {email_id}"
    }
    
    return session_info


def update_session_state(
    session_id: str,
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Updates an existing session's state with new data.
    
    Args:
        session_id: str -> The session ID to update
        updates: Dict -> Key-value pairs to update in the state
    
    Returns:
        Dict containing update status and new state
    """
    
    # In a real implementation, this would interact with your session service
    # For now, we'll return a mock response
    
    updated_at = datetime.utcnow().isoformat()
    
    return {
        "status": "success",
        "session_id": session_id,
        "updated_at": updated_at,
        "updates_applied": list(updates.keys()),
        "message": f"Session {session_id} updated successfully"
    }


def get_session_info(session_id: str) -> Dict[str, Any]:
    """
    Retrieves information about an existing session.
    
    Args:
        session_id: str -> The session ID to retrieve
    
    Returns:
        Dict containing session information
    """
    
    # In a real implementation, this would query your session service
    # For now, we'll return a mock response
    
    return {
        "status": "success",
        "session_id": session_id,
        "message": f"Session {session_id} information retrieved",
        "note": "This is a mock response. Implement actual session service integration."
    } 