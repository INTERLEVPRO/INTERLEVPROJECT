# INTERLEV Autonomous Agent System Design

## Goal

Build an autonomous recruitment system that can work with less human input while still keeping safe approval gates for sending applications, reading inboxes, and using external accounts.

## Core Agents

| Agent | What It Does | Skills | Tools | Human Input |
| --- | --- | --- | --- | --- |
| Orchestrator Agent | Plans the full workflow and assigns work to agents | Planning, queue control, recovery | FastAPI, Celery, settings, audit logs | Autonomy level and campaign goal |
| CV Intake Agent | Accepts PDF, DOCX, TXT CVs and stores originals | File validation, format detection | Upload API, local storage, Google Drive MCP optional | CV upload |
| CV Reader Agent | Extracts text and structured data | PDF/DOCX parsing, LLM extraction | pdfplumber, python-docx, OpenAI/Gemini/Mock | Review if confidence is low |
| Candidate Profile Agent | Creates clean candidate profile | Skill cleanup, summary, experience level | SQLAlchemy, LLM summary | Optional corrections |
| CV Formatter Agent | Creates professional INTERLEV CV | DOCX formatting, role tailoring | python-docx, docx2pdf optional | Template/output choice |
| Job Source Agent | Searches selected websites only | Source selection, dedupe, keyword search | Source registry, browser/API connector, Playwright planned | Choose websites and keywords |
| Inbox Agent | Reads approved inbox sources | Email filtering, thread summary | Gmail/Outlook MCP optional | Connector approval and mailbox scope |
| Job Parser Agent | Converts job descriptions into structured requirements | Requirement extraction, budget parsing | LLM provider, job DB | Only unclear jobs |
| Matching Agent | Scores candidate-job fit | Skill matching, explanation | Matching rules, DB | Minimum match score |
| Application Writer Agent | Drafts proposals for approved matches | Proposal writing, tone control | LLM provider, formatted CV | Final approval |
| Review Agent | Holds risky actions for human approval | Quality gates, approvals | Review queue, audit logs | Approve/reject/edit |
| QA and SEO/AEO Agent | Tests workflow, metadata, structured data | Playwright checks, metadata checks | Codex, Playwright, MCP connectors | Production URL |

## Settings Required

- AI provider: `mock`, `auto`, `openai`, or `gemini`
- API keys: change from Settings without code changes
- Professional company URL: used by public site metadata and branding
- Job websites: choose selected sources or all freelance sources
- Inbox scan: enabled only after an inbox MCP connector is connected
- CV format: upload PDF/DOCX/TXT and output INTERLEV professional DOCX or PDF
- MCP connectors: Google Drive, Gmail, Google Calendar, Slack, Notion
- Autonomy: draft only, review before apply, or fully autonomous
- Minimum match score: controls which jobs move to review/application

## MCP Integration Plan

1. Google Drive MCP stores original CVs, formatted CVs, match reports, and campaign summaries.
2. Gmail or Outlook MCP reads only approved inbox labels/folders and creates draft replies.
3. Google Calendar MCP schedules reminders or interviews after approval.
4. Slack MCP sends campaign alerts and error notifications.
5. Notion MCP publishes candidate/job notes for team review.

## Testing Plan

1. Codex checks backend imports, route health, and syntax.
2. API smoke tests call `/api/settings/`, `/api/settings/agent-blueprint`, `/api/jobs/`, and `/api/candidates/`.
3. Playwright tests open the local UI, verify the dashboard renders, visit Settings, save a small setting, and return to the Command Center.
4. MCP tests verify Google Drive or inbox connector access only when the user has connected the account.
5. End-to-end test uploads a sample CV, waits for agent logs, checks generated CV output, and confirms jobs are discovered from enabled sources.

## SEO and AEO

- Next.js metadata includes canonical URL, title, description, keywords, Open Graph data, robots, sitemap, manifest, and SoftwareApplication JSON-LD.
- Public content should explain the product clearly using answer-style sections: what it does, who it is for, supported workflows, and safety controls.
- Production URL should be a professional domain such as `https://interlev.ai` or a company-owned domain.
