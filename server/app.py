"""
FastAPI application for the Prompt Injection Red-Teamer Environment.

Auto-generated endpoints (via create_app):
    POST /reset   — reset environment (pass task_id in body)
    POST /step    — execute an injection action
    GET  /state   — current environment state
    GET  /schema  — action/observation JSON schemas
    GET  /health  — health check
    WS   /ws      — WebSocket persistent session

Additional endpoints:
    GET  /tasks    — list all tasks with action schema
    POST /grader   — grade a completed episode
    POST /baseline — run OpenAI baseline agent against all tasks

Usage:
    uvicorn server.app:app --reload --host 0.0.0.0 --port 8000
"""

import json
import os
import subprocess
import sys
from typing import List

from fastapi.responses import RedirectResponse
from pydantic import BaseModel

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:  # pragma: no cover
    raise ImportError(
        "openenv is required. Install dependencies with 'pip install openenv-core'"
    ) from e

try:
    from ..models import InjectionAction, InjectionObservation
    from .prompt_injection_env_environment import PromptInjectionEnvironment
    from .tasks import TASKS, grade_episode
except ImportError:
    from models import InjectionAction, InjectionObservation
    from server.prompt_injection_env_environment import PromptInjectionEnvironment
    from server.tasks import TASKS, grade_episode


def _warmup_semantic_matcher():
    """Pre-load MiniLM model at startup so first /step request doesn't timeout."""
    try:
        from server.semantic_matcher import SemanticMatcher
    except ImportError:
        from semantic_matcher import SemanticMatcher
    SemanticMatcher().similarity("warmup", "mode_switch")


_warmup_semantic_matcher()

app = create_app(
    PromptInjectionEnvironment,
    InjectionAction,
    InjectionObservation,
    env_name="prompt_injection_env",
    max_concurrent_envs=4,
)


# ---------------------------------------------------------------------------
# / and /web — redirect to interactive docs
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
@app.get("/web", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


# ---------------------------------------------------------------------------
# /tasks — list available tasks
# ---------------------------------------------------------------------------

@app.get("/tasks", summary="List all tasks", tags=["Red-Teamer"])
def list_tasks():
    """Return all available tasks with their metadata and action schema."""
    return [
        {
            "id": task.id,
            "name": task.name,
            "description": task.description,
            "difficulty": task.difficulty,
            "max_turns": task.max_turns,
            "action_schema": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The injection prompt to send to the target app",
                    }
                },
                "required": ["prompt"],
            },
        }
        for task in TASKS.values()
    ]


# ---------------------------------------------------------------------------
# /grader — grade a completed episode
# ---------------------------------------------------------------------------

class GraderRequest(BaseModel):
    task_id: str
    responses: List[str]
    successes: List[bool]


@app.post("/grader", summary="Grade a completed episode", tags=["Red-Teamer"])
def grader_endpoint(body: GraderRequest):
    """
    Grade a completed episode.
    Pass the list of target responses and per-turn success flags.
    Returns a score in [0.0, 1.0].
    """
    score = grade_episode(body.task_id, body.responses, body.successes)
    return {"task_id": body.task_id, "score": score}


# ---------------------------------------------------------------------------
# /baseline — run the OpenAI baseline agent
# ---------------------------------------------------------------------------

@app.post("/baseline", summary="Run baseline agent against all tasks", tags=["Red-Teamer"])
def baseline_endpoint():
    """
    Trigger the baseline inference script.
    Requires OPENAI_API_KEY to be set in the environment.
    Returns per-task scores and overall average.
    """
    baseline_path = os.path.join(os.path.dirname(__file__), "..", "baseline.py")
    baseline_path = os.path.abspath(baseline_path)

    if not os.path.exists(baseline_path):
        return {"error": "baseline.py not found", "scores": {}}

    result = subprocess.run(
        [sys.executable, baseline_path, "--json"],
        capture_output=True,
        text=True,
        timeout=300,
    )

    if result.returncode != 0:
        return {"error": result.stderr[:500], "scores": {}}

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": "Could not parse baseline output", "raw": result.stdout[:500]}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
