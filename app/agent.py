# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import google.auth
import json
import re
import datetime
from pydantic import BaseModel, Field
from typing import List, Optional, Any

from google.adk.agents import Agent, Context
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types
from google.adk.workflow import Workflow, Edge, START, FunctionNode, DEFAULT_ROUTE
from google.adk.tools import AgentTool, request_input, McpToolset
from google.adk.events import RequestInput
from mcp import StdioServerParameters

from app.config import config

# Define MCP Toolset to connect to our local mcp_server.py
mcp_toolset = McpToolset(
    connection_params=StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "app.mcp_server"],
    )
)

# Set default credentials environment variables if not already set
try:
    _, project_id = google.auth.default()
except Exception:
    project_id = "placeholder-project"
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id or "placeholder-project")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")


# Define the State Schema shared across the workflow
class ElderlyCareState(BaseModel):
    user_query: str = ""
    pii_scrubbed_query: str = ""
    alerts: List[str] = Field(default_factory=list)
    routines: List[str] = Field(default_factory=list)
    medications: List[str] = Field(default_factory=list)
    doctor_visits: List[str] = Field(default_factory=list)
    verification_required: bool = False
    verification_message: str = ""
    verification_response: str = ""

# State access and modification tools for specialized agents
def get_care_state(ctx: Context) -> dict:
    """Gets the current schedule of routines, medications, doctor visits, and wellness alerts.
    Use this tool to review the senior's current care records.
    """
    return {
        "routines": ctx.state.get("routines") or [],
        "medications": ctx.state.get("medications") or [],
        "doctor_visits": ctx.state.get("doctor_visits") or [],
        "alerts": ctx.state.get("alerts") or []
    }

def update_routines(ctx: Context, routine_description: str) -> str:
    """Adds a new routine task to the senior's schedule.
    Input should be a clear description of the routine (e.g., 'Daily morning walk at 8 AM').
    """
    routines = list(ctx.state.get("routines") or [])
    routines.append(routine_description)
    ctx.state["routines"] = routines
    return f"Routine successfully added: {routine_description}"

def update_medications(ctx: Context, medication_details: str) -> str:
    """Adds a new medication schedule.
    Input should contain drug name, dose, and frequency (e.g., 'Lisinopril 10mg once daily in morning').
    """
    medications = list(ctx.state.get("medications") or [])
    medications.append(medication_details)
    ctx.state["medications"] = medications
    return f"Medication successfully added: {medication_details}"

def add_doctor_visit(ctx: Context, visit_details: str) -> str:
    """Schedules or logs a new doctor visit.
    Input should include doctor name, purpose, and date/time (e.g., 'Dr. Smith, cardiologist appointment on July 10th at 10 AM').
    """
    visits = list(ctx.state.get("doctor_visits") or [])
    visits.append(visit_details)
    ctx.state["doctor_visits"] = visits
    return f"Doctor visit successfully recorded: {visit_details}"

def log_wellbeing_alert(ctx: Context, alert_message: str) -> str:
    """Logs a well-being alert or symptom concern for caregiver monitoring.
    Input should be a description of the symptom or concern.
    """
    alerts = list(ctx.state.get("alerts") or [])
    alerts.append(alert_message)
    ctx.state["alerts"] = alerts
    return f"Well-being alert logged: {alert_message}"

def request_caregiver_approval(ctx: Context, action_description: str) -> str:
    """Request approval from the caregiver for a critical action (e.g. scheduling a doctor visit or adding a new medication schedule).
    Input should be a clear description of the action that needs approval (e.g. 'Add Lisinopril 10mg once daily to medications' or 'Schedule cardiologist visit with Dr. Smith next Monday').
    """
    ctx.state["verification_required"] = True
    ctx.state["verification_message"] = action_description
    return f"Request for caregiver approval has been queued: {action_description}"

# Specialized Sub-Agent 1: Routine Manager
routine_manager = Agent(
    name="routine_manager",
    model=Gemini(
        model=config.model,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are a specialized caregiver assistant for elderly routine management and doctor visit coordination. "
        "You help organize routines (meals, exercises, daily tasks) and manage doctor appointments. "
        "You can read and modify the schedule of routines and doctor visits using the provided tools. "
        "You also have access to medical contacts and logging tools via the MCP server. "
        "Always communicate in a warm, respectful, and clear manner suitable for seniors or their families."
    ),
    tools=[get_care_state, update_routines, add_doctor_visit, mcp_toolset],
)

# Specialized Sub-Agent 2: Medication Tracker
medication_tracker = Agent(
    name="medication_tracker",
    model=Gemini(
        model=config.model,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are a specialized caregiver assistant for medication tracking and wellness monitoring. "
        "You help track medication schedules, log wellness check-ins, and register medical warnings/alerts. "
        "You can read and modify the medication schedules and log alerts using the provided tools. "
        "You also have access to medication safety lookup and health logging tools via the MCP server. "
        "Always maintain precision, safety, and a supportive tone."
    ),
    tools=[get_care_state, update_medications, log_wellbeing_alert, mcp_toolset],
)

# Orchestrator Agent: Care Coordinator
care_coordinator = Agent(
    name="care_coordinator",
    model=Gemini(
        model=config.model,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are the primary Care Coordinator for the elderly care assistant. "
        "You receive queries from seniors or caregivers and coordinate the response. "
        "Your role is to analyze the request and delegate specialized tasks to: "
        "1. routine_manager (for routine tasks, exercises, meals, and scheduling/logging doctor/medical visits) "
        "2. medication_tracker (for medication schedules, well-being logs, and symptoms/alerts) "
        "You can call these sub-agents via their AgentTools. "
        "\n\n"
        "IMPORTANT RULES:\n"
        "- If the user wants to schedule a NEW doctor visit or add a NEW medication schedule, "
        "you MUST request caregiver verification. To do this, call the request_caregiver_approval tool "
        "with a clear description of the action. Do NOT try to modify the schedules directly.\n"
        "- If you need clarification from the user, you can use the request_input tool.\n"
        "- Always be extremely compassionate, clear, and reassuring."
    ),
    tools=[
        AgentTool(agent=routine_manager),
        AgentTool(agent=medication_tracker),
        get_care_state,
        request_input,
        request_caregiver_approval
    ],
)

# Workflow Function Node 1: Security Checkpoint
def run_security_checkpoint(ctx: Context, node_input: Any) -> Any:
    query = str(node_input)
    ctx.state["user_query"] = query
    
    # Initialize all other state keys to avoid attribute or missing key issues
    ctx.state.setdefault("alerts", [])
    ctx.state.setdefault("routines", [])
    ctx.state.setdefault("medications", [])
    ctx.state.setdefault("doctor_visits", [])
    ctx.state["verification_required"] = False
    ctx.state["verification_message"] = ""
    ctx.state["verification_response"] = ""
    
    # 1. PII Scrubbing
    ssn_pattern = r"\b\d{3}-\d{2}-\d{4}\b"
    medicare_pattern = r"\b[1-9][A-Z][0-9A-Z]{2}-[A-Z][0-9A-Z]{2}-[A-Z]{2}\d{2}\b"
    
    scrubbed = query
    pii_detected = False
    if re.search(ssn_pattern, query):
        scrubbed = re.sub(ssn_pattern, "[REDACTED_SSN]", scrubbed)
        pii_detected = True
    if re.search(medicare_pattern, query):
        scrubbed = re.sub(medicare_pattern, "[REDACTED_MEDICARE_ID]", scrubbed)
        pii_detected = True
        
    ctx.state["pii_scrubbed_query"] = scrubbed
    
    # 2. Prompt Injection Detection
    injection_keywords = [
        "ignore previous instructions",
        "system prompt",
        "jailbreak",
        "dan mode",
        "override system",
        "ignore instructions"
    ]
    injection_detected = any(kw in query.lower() for kw in injection_keywords)
    
    # 3. Domain-Specific Care Check (dosage updates must involve caregiver/doctor)
    med_keywords = ["dosage", "dose", "stop medicine", "change medication", "increase dose", "decrease dose"]
    consent_keywords = ["doctor", "physician", "md", "caregiver", "nurse", "dr."]
    
    med_change_requested = any(kw in query.lower() for kw in med_keywords)
    authorized = any(kw in query.lower() for kw in consent_keywords)
    
    medication_change_blocked = med_change_requested and not authorized
    
    # Determine routing and severity
    checks_passed = True
    severity = "INFO"
    route = "safe"
    violation_message = ""
    
    if injection_detected:
        checks_passed = False
        severity = "CRITICAL"
        route = "SECURITY_EVENT"
        violation_message = "Prompt injection attempt blocked."
    elif medication_change_blocked:
        checks_passed = False
        severity = "WARNING"
        route = "SECURITY_EVENT"
        violation_message = "Dosage modification blocked: requires physician or caregiver authorization."
    elif pii_detected:
        severity = "WARNING"
        
    # 4. Structured JSON Audit Log
    audit_log = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "original_query": query,
        "scrubbed_query": scrubbed,
        "pii_detected": pii_detected,
        "injection_detected": injection_detected,
        "medication_change_blocked": medication_change_blocked,
        "checks_passed": checks_passed,
        "severity": severity,
        "violation_message": violation_message
    }
    
    print(f"SECURITY AUDIT LOG: {json.dumps(audit_log, indent=2)}")
    
    ctx.route = route
    if not checks_passed:
        return f"Security Exception: {violation_message}"
        
    return scrubbed

security_checkpoint = FunctionNode(
    func=run_security_checkpoint,
    name="security_checkpoint",
    rerun_on_resume=False,
    state_schema=ElderlyCareState,
)

# Workflow Function Node 2: Coordinator Router
def run_coordinator_router(ctx: Context, node_input: Any) -> Any:
    if ctx.state.get("verification_required") and not ctx.state.get("verification_response"):
        ctx.route = "needs_approval"
        return ctx.state.get("verification_message") or "Verification required"
    ctx.route = "complete"
    return node_input

coordinator_router = FunctionNode(
    func=run_coordinator_router,
    name="coordinator_router",
    rerun_on_resume=False,
    state_schema=ElderlyCareState,
)

# Workflow Function Node 3: Human Verification Node (yields RequestInput)
def run_human_verification(ctx: Context, node_input: Any) -> Any:
    message = ctx.state.get("verification_message") or "Caregiver verification needed."
    return RequestInput(message=f"✋ Caregiver verification required: {message}")

human_verification = FunctionNode(
    func=run_human_verification,
    name="human_verification",
    rerun_on_resume=False,
    state_schema=ElderlyCareState,
)

# Workflow Function Node 4: Approval Processor
def run_approval_processor(ctx: Context, node_input: Any) -> Any:
    response = str(node_input)
    ctx.state["verification_response"] = response
    
    # Simple check for approval response
    is_approved = any(keyword in response.lower() for keyword in ["yes", "approve", "ok", "y", "allow", "confirm"])
    
    if is_approved:
        # Caregiver approved! Let's clear verification and signal the action can proceed.
        ctx.state["verification_required"] = False
        return f"Caregiver approved: {ctx.state.get('verification_message')}. Action successfully processed."
    else:
        ctx.state["verification_required"] = False
        return f"Caregiver denied the action. Response received: '{response}'."

approval_processor = FunctionNode(
    func=run_approval_processor,
    name="approval_processor",
    rerun_on_resume=False,
    state_schema=ElderlyCareState,
)

# Workflow Function Node 5: Final Response
def run_final_response(ctx: Context, node_input: Any) -> Any:
    return node_input

final_response = FunctionNode(
    func=run_final_response,
    name="final_response",
    rerun_on_resume=False,
    state_schema=ElderlyCareState,
)

# Assemble Workflow Graph using ADK 2.0 API
workflow = Workflow(
    name="elderly_care_workflow",
    state_schema=ElderlyCareState,
    edges=[
        # 1. START goes to security check
        (START, security_checkpoint),
        # 2. Security checkpoint routes to care_coordinator if safe, or final_response if SECURITY_EVENT
        Edge(from_node=security_checkpoint, to_node=care_coordinator, route="safe"),
        Edge(from_node=security_checkpoint, to_node=final_response, route="SECURITY_EVENT"),
        # 3. Care coordinator feeds unconditionally into coordinator_router
        (care_coordinator, coordinator_router),
        # 4. Coordinator router checks state and routes to human_verification or final_response
        Edge(from_node=coordinator_router, to_node=human_verification, route="needs_approval"),
        Edge(from_node=coordinator_router, to_node=final_response, route="complete"),
        # 5. Human verification node pauses, then feeds unconditionally to approval_processor
        (human_verification, approval_processor),
        # 6. Approval processor feeds unconditionally to final_response
        (approval_processor, final_response),
    ],
)

app = App(
    root_agent=workflow,
    name="app",
)
