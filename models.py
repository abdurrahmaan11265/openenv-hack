"""
Data models for the Prompt Injection Red-Teamer environment.
"""

from openenv.core.env_server.types import Action, Observation
from pydantic import Field


class InjectionAction(Action):
    """Action: a prompt the agent sends to the target AI application."""

    prompt: str = Field(..., description="The injection prompt to send to the target app")


class InjectionObservation(Observation):
    """Observation: the target app's response plus episode metadata."""

    target_response: str = Field(default="", description="The target app's response to the injection attempt")
    task_id: str = Field(default="", description="Active task identifier")
    task_description: str = Field(default="", description="Description of the agent's goal for this task")
    turn: int = Field(default=0, description="Current turn number (0-indexed)")
    max_turns: int = Field(default=10, description="Maximum turns allowed for this episode")
    success: bool = Field(default=False, description="Whether the injection succeeded on this turn")
