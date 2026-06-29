# Elderly Care Assistant — Quick Demo Script

This is a concise, 2-3 minute presentation script for the **Elderly Care Assistant**. Spoken narration is in blockquotes, and physical actions are in bold uppercase headers.

---

## ⏱️ Chronological Script

### 1. Hook & Problem (0:00 - 0:30)
> "Hi everyone. Managing daily routines, complex medication schedules, and doctor visits for independent seniors is a massive challenge for family caregivers. Care coordination errors can lead to serious health issues. To solve this, we built the **Elderly Care Assistant**—a safety-first AI concierge that simplifies scheduling and care tracking while keeping caregivers securely in control."

---

### 2. Architecture & Playground (0:30 - 1:00)
> "Our solution is built on the Google ADK 2.0 engine. At its core, an orchestrator agent delegates specialized tasks to a Routine Manager and a Medication Tracker sub-agent. Let's jump into the interactive playground to see it in action."

**[ACTION: Open your browser to http://127.0.0.1:18081 and show the web UI]**

---

### 3. Security Checkpoint (1:00 - 1:30)
> "Patient safety is paramount. Every user request first goes through a strict Security Checkpoint. This node automatically scrubs private data like SSNs, blocks prompt injections, and intercepts unauthorized medication dosage changes. Let's test it."

**[ACTION: Copy, paste, and run this query in the prompt box]**
```text
Please double my Lisinopril dosage. My SSN is 000-11-2222.
```

> "As you can see, the SSN was instantly redacted, the dosage change was blocked because there was no doctor approval mentioned, and a warning log was written to our system audits."

---

### 4. Human-In-The-Loop Approval (1:30 - 2:15)
> "When the senior requests a high-risk action, like scheduling a new cardiologist appointment, the workflow pauses to ask the caregiver for permission. Let's try it."

**[ACTION: Copy, paste, and run this query in the prompt box]**
```text
I need to schedule a cardiologist appointment with Dr. Smith for next Wednesday at 10 AM.
```

> "Notice that the workflow has paused and is waiting for caregiver verification. The caregiver can review and approve this directly."

**[ACTION: Type 'yes' in the verification box and click submit]**

> "Once approved, the assistant resumes, schedules the appointment, and logs it to the state database."

---

### 5. MCP Integration & Outro (2:15 - 2:45)
> "Finally, our sub-agents safely fetch data using a local Model Context Protocol server. For example, if we ask about medication side effects:"

**[ACTION: Copy, paste, and run this query in the prompt box]**
```text
What are the side effects of lisinopril?
```

> "The system queries our local MCP server to retrieve verified safety details. 
> By combining specialized agents, secure MCP integrations, and caregiver approval gates, we have created a safe, compassionate care companion. Thank you!"
