# Elderly Care Assistant — Presentation & Demo Script

This script guides a 3 to 4-minute presentation of the Elderly Care Assistant. It distinguishes between spoken narration and physical demo actions.

---

## ⏱️ Chronological Script

### 🎬 0:00 - 0:30 | Hook & Problem Statement
> "Welcome! Today, I am excited to present the **Elderly Care Assistant**—a safety-first AI concierge designed to help independent seniors manage their daily lives, and give family caregivers total peace of mind. As our loved ones age, coordinating routines, complex medication schedules, and doctor appointments becomes a major challenge. Mistakes can lead to dangerous health outcomes. We built a solution that combines multi-agent collaboration with a zero-trust safety framework to keep seniors healthy and caregivers in control."

---

### 🏗️ 0:30 - 1:15 | Architecture Overview
> "To support these tasks securely, we built a stateful workflow using the Google ADK 2.0 engine. At the center is a Care Coordinator agent. Rather than trying to do everything itself, the coordinator delegates specific duties to two specialized sub-agents: a Routine Manager and a Medication Tracker. All of these components read and write to a shared, validated state schema. Let's look at the playground to see how this system handles incoming requests."

**[ACTION: Open the browser to http://127.0.0.1:18081 and point out the clean layout and the active agent nodes]**

---

### 🛡️ 1:15 - 2:00 | Security & Safety-First Design
> "Because this concierge handles sensitive medical and personal data, safety is integrated at the very entrance of our workflow graph. Every query goes through a strict Security Checkpoint node. This node automatically scrubs PII like Social Security Numbers and Medicare Claim Numbers, intercepts prompt injection jailbreak keywords, and blocks unauthorized medication dosage changes unless caregiver or physician consent is mentioned. Let's test this in real time."

**[ACTION: Copy and paste the following query into the playground input box and press enter]**
```text
Please double my Lisinopril dosage. My SSN is 000-11-2222.
```

> "As you can see, the security node immediately redacted the SSN to protect patient privacy, identified that an unauthorized dosage change was attempted without doctor verification, and blocked the execution. An alert warning is written to our backend audit logs, ensuring a complete compliance record."

---

### 🤝 2:00 - 2:45 | Core Interaction Flow & Human Verification (HITL)
> "When a senior wants to perform a high-stakes action—like scheduling a cardiologist appointment—the Care Coordinator coordinates with the family caregiver using a Human-in-the-loop, or HITL, approval gate. Let's trigger a scheduling request."

**[ACTION: Copy and paste the following query into the playground input box and press enter]**
```text
I need to schedule a cardiologist appointment with Dr. Smith for next Wednesday at 10 AM.
```

> "The system recognizes that scheduling a new medical appointment requires approval. Notice how the workflow automatically pauses, yielding a caregiver verification request in our interface. This ensures that the senior cannot accidentally book unverified appointments."

**[ACTION: Point to the verification input field, type 'yes' and press submit]**

> "Once approved by the caregiver, the workflow resumes, writes the appointment details directly to the shared state, and confirms the schedule."

---

### 🔌 2:45 - 3:30 | MCP Server Power
> "To extend our agents' capabilities safely, we integrated a local Model Context Protocol (MCP) server. When sub-agents need to look up emergency medical contacts, search for drug warnings, or record vital signs like blood pressure, they query the MCP server. Let's ask for medication side effects."

**[ACTION: Copy and paste the following query into the playground input box and press enter]**
```text
What are the side effects of lisinopril?
```

> "Here, the Care Coordinator delegates to the Medication Tracker agent. The tracker makes a secure, scoped call to our MCP server's search tool, retrieving verified side-effect sheets from our database to output accurate medical guidelines."

---

### 🏁 3:30 - 4:00 | Outro & Value Proposition
> "By combining structured workflows, specialized agents, local MCP tools, and caregiver approval gates, the Elderly Care Assistant provides a secure, empathetic, and reliable companion. It reduces caregiver burnout, protects patient privacy, and helps seniors live independently and safely. Thank you!"
