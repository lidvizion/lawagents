# Law Firm Tools & Technologies

**Target:** Small to mid-sized law firms ($2M–$50M annual revenue)  
**Purpose:** Inventory of tools with MCP, APIs, and integration points for agent-driven workflows. Pairs with [Law Firm Roles & Skills](law-firm-roles-and-skills.md). Designed for autonomous agent execution with check-ins, approvals, and guardrails.

---

## 1. Clio (Practice Management)

**Primary system** for matters, contacts, billing, calendar, and documents. Start here; branch to other tools from Clio.

### Overview

| Aspect | Details |
|--------|---------|
| **Product** | Clio Manage (practice management), Clio Grow (intake/CRM) |
| **Docs** | [Clio Developer Documentation](https://docs.developers.clio.com/) |
| **Auth** | OAuth 2.0 (Authorization Code grant) |
| **MCP** | Yes—via [Zapier Clio MCP](https://zapier.com/mcp/clio) |

### API Capabilities

| Resource | Operations | Agent-Ready Use Cases |
|----------|-------------|------------------------|
| **Matters** | CRUD, list, search | Matter creation, status summaries, matter profitability, conflict checks |
| **Contacts** | CRUD, email/phone, related | Client/contact sync, intake data, CRM updates |
| **Tasks** | CRUD, templates | Task creation, matter task lists, delegation, deadlines |
| **Calendar** | Calendars, entries, reminders | Scheduling, court dates, consultation booking |
| **Time Entries** | Create, list, update | Time capture, billing prep, matter profitability |
| **Activities** | With rates, descriptions | Billing codes, UTBMS, activity tracking |
| **Bills** | Create, list, update | Invoice generation, aging, write-off analysis |
| **Expenses** | Categories, entries | Expense tracking, matter cost allocation |
| **Documents** | Store, retrieve | Document management, matter file linking |

### MCP (Zapier Integration)

| Action | Description | Approval Level |
|--------|-------------|----------------|
| Create matter | New matter with client, matter type | Medium |
| Create calendar entry | Event, deadline, reminder | Low |
| Create task | Matter task, deadline | Low |
| Create/update contact | Company or person contact | Low |
| Create matter folder | Document organization | Low |
| Manage task templates | Reusable task templates | Medium |
| Create expense entry | Matter expense | Medium |

### API Features

- **Fields parameter**: Request only needed fields; default is `id` and `etag`
- **Pagination**: Max 200 results per request
- **ETags**: Detect changes since last sync
- **Rate limits**: Per-request limits; 429 when exceeded
- **Webhooks**: Event notifications for changes
- **Permissions**: OAuth scopes per resource (read vs read/write)

### Getting Started

1. Create app in [Clio Developer Portal](https://staging.api.clio.com/)
2. Configure redirect URIs and OAuth scopes
3. Implement OAuth flow; store access token
4. Use MCP URL from Zapier for MCP-aware AI tools (no custom code)

### Role Mapping (from Law Firm Roles)

| Role | Primary Clio Use Cases |
|------|------------------------|
| Managing Partner | Matter profitability, firm KPIs, dashboards |
| Partners | Matter status, client data, billing review |
| Associates | Time entries, tasks, calendar, matter docs |
| Billing/Finance Manager | Bills, time entries, aging, write-offs |
| Legal Intake Specialist | Contacts, matters, intake → matter creation |
| Paralegal | Tasks, documents, matter folders |
| Legal Secretary | Calendar, tasks, documents |

### Guardrails & Approvals

| Action | Suggested Guardrail |
|--------|---------------------|
| Create matter | Require partner/COO approval before creation |
| Create bill / send invoice | Require billing manager or partner approval |
| Delete matter/contact | Require confirmation + audit log |
| Bulk updates | Require review and approval workflow |
| Time entry write-offs | Require partner approval |

---

## 2. Branching from Clio

*(To be expanded as we add other tools.)*

| Tool Category | Next Additions | Integration Path |
|---------------|----------------|------------------|
| **CRM / Intake** | Clio Grow, Zapier | Clio Grow API or Zapier |
| **Communications** | Slack, Email | Zapier, Slack MCP |
| **Project Management** | Linear | Linear MCP |
| **Database / Backend** | Supabase | Supabase MCP |
| **E-Discovery** | TBD | API or Zapier |
| **Document Storage** | Google Drive, Dropbox | Zapier, native APIs |

---

## 3. Check-In Protocols

| Agent Action | Check-In Type | When |
|--------------|---------------|------|
| Create matter | Approval | Before creation |
| Send invoice | Approval | Before send |
| Create/update contact | Optional review | Low risk; log for audit |
| Create task/calendar entry | Optional review | Low risk; log for audit |
| Bulk operations | Mandatory approval | Always |
| Delete operations | Mandatory approval | Always |
| Read-only queries | Log only | No approval needed |

---

## 4. References

- [Clio Manage API](https://docs.developers.clio.com/api-docs/clio-manage/)
- [Clio Authorization](https://docs.developers.clio.com/api-docs/clio-manage/authorization/)
- [Clio Permissions](https://docs.developers.clio.com/api-docs/clio-manage/permissions/)
- [Zapier Clio MCP](https://zapier.com/mcp/clio)
- [Clio Integrations (250+ apps)](https://www.clio.com/features/integrations/)
