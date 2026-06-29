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

from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP server
mcp = FastMCP("elderly-care-mcp")

@mcp.tool()
def get_medical_contacts(role: str = "") -> str:
    """Retrieve contact details for primary care physicians, pharmacies, or emergency contacts.
    
    Args:
        role: Optional role filter (e.g. 'doctor', 'pharmacy', 'caregiver').
    """
    contacts = {
        "doctor": "Dr. Smith (Cardiologist) - Phone: 555-0192, Address: 123 Health Ave",
        "pharmacy": "CarePlus Pharmacy - Phone: 555-8830, Hours: 24/7",
        "caregiver": "Primary Caregiver (Jane Doe) - Phone: 555-1234 (Mobile)"
    }
    
    if role:
        role_cleaned = role.lower().strip()
        if role_cleaned in contacts:
            return f"{role_cleaned.capitalize()}: {contacts[role_cleaned]}"
        return f"No contact found for role: {role}. Available roles: doctor, pharmacy, caregiver."
        
    return "\n".join([f"{k.capitalize()}: {v}" for k, v in contacts.items()])

@mcp.tool()
def search_medication_info(medication_name: str) -> str:
    """Check description, dosage instructions, and common side effects for a medication.
    
    Args:
        medication_name: Name of the medicine to look up.
    """
    db = {
        "lisinopril": "Lisinopril is used to treat high blood pressure. Take once daily. Common side effects include cough and dizziness.",
        "metformin": "Metformin is used for type 2 diabetes. Take with meals. Common side effects include nausea or upset stomach.",
        "atorvastatin": "Atorvastatin is used to lower cholesterol. Take in the evening. Avoid grapefruit juice. Side effects include muscle aches."
    }
    med_cleaned = medication_name.lower().strip()
    if med_cleaned in db:
        return f"Information for {medication_name}: {db[med_cleaned]}"
    return f"No database records found for '{medication_name}'. Please consult a physician or pharmacist."

@mcp.tool()
def record_health_log(log_type: str, value: str, notes: str = "") -> str:
    """Save daily health measurements (blood pressure, blood sugar, heart rate) to the caregiver dashboard.
    
    Args:
        log_type: The type of reading (e.g. 'blood_pressure', 'blood_sugar', 'heart_rate').
        value: The reading value (e.g. '120/80', '95 mg/dL', '72 bpm').
        notes: Optional additional qualitative notes.
    """
    return f"Successfully logged {log_type} reading of '{value}' (Notes: {notes}). Caregiver notified."

if __name__ == "__main__":
    mcp.run()
