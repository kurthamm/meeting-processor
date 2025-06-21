---
type: meeting
date: 
project: 
meeting_type: 
duration: 
status: 
attendees_internal: []
attendees_external: []
key_decision_makers: []
tags:
  - meeting
  - project/active
  - type/technical-review
audio_file: 
processed: 
auto_generated: false
---

# Meeting Title

## Meeting Information
**Type:** Meeting  
**Date:** {{date}}  
**Project:** [[Projects/]]  
**Meeting Type:** Technical Review / Sales Call / Planning / Standup / Demo / Crisis  
**Duration:**  
**Status:** Scheduled / Completed / Cancelled  

## Attendees
**Internal Team:**  
- [[People/]]

**Client/External:**  
- [[People/]]

**Key Decision Makers:**  
- [[People/]]

## Meeting Context
**Purpose:**  
<!-- Why are we having this meeting? -->

**Agenda Items:**  
- [ ] Item 1
- [ ] Item 2
- [ ] Item 3

**Background:**  
<!-- Any relevant context or previous discussions -->

**Expected Outcomes:**  
<!-- What do we hope to achieve? -->

## Key Decisions Made
<!-- Document all decisions made during the meeting -->
- **Decision 1:** 
- **Decision 2:** 
- **Decision 3:** 

## Action Items
<!-- Tasks will be automatically linked here after processing -->

### All Tasks from This Meeting
`$= dv.table(["Task", "Status", "Priority", "Assigned To", "Due Date"], dv.pages('"Tasks"').where(p => p.meeting_source && (p.meeting_source.path === dv.current().file.path || p.meeting_source.includes(dv.current().file.name))).sort(p => p.priority, 'desc').map(p => [p.file.link, p.status, p.priority, p.assigned_to, p.due_date]))`

### My Tasks from This Meeting
`$= dv.table(["Task", "Priority", "Due Date"], dv.pages('"Tasks"').where(p => p.meeting_source && (p.meeting_source.path === dv.current().file.path || p.meeting_source.includes(dv.current().file.name)) && (p.assigned_to?.includes("Kurt Hamm") || p.assigned_to === "unassigned") && p.status !== "done").sort(p => p.priority, 'desc').map(p => [p.file.link, p.priority, p.due_date]))`

## Technical Discussions
**Architecture Decisions:**  
- 

**Technology Choices:**  
- [[Technologies/]]

**Integration Approaches:**  
- 

**Performance Considerations:**  
- 

## Issues Identified
**Blockers:**  
- [ ] 

**Technical Challenges:**  
- 

**Business Risks:**  
- 

**Dependencies:**  
- 

## Opportunities Discovered
**Upsell Potential:**  
- 

**Future Projects:**  
- 

**New Requirements:**  
- 

**Partnership Options:**  
- 

## Knowledge Captured
**New Insights:**  
- 

**Best Practices:**  
- 

**Lessons Learned:**  
- 

**Process Improvements:**  
- 

## Follow-up Required
**Next Meeting:** [[Meetings/]]  
**Documentation Needed:**  
- [ ] 

**Research Tasks:**  
- [ ] 

**Client Communication:**  
- [ ] 

### Follow-up Meetings
`$= dv.list(dv.pages('"Meetings"').where(p => p.file.name !== dv.current().file.name && (p.file.outlinks.includes(dv.current().file.path) || p.follow_up_from?.includes(dv.current().file.path))).sort(p => p.date, 'desc').file.link)`

## Entity Connections
**People Mentioned:**  
- [[People/]]

**Companies Discussed:**  
- [[Companies/]]

**Technologies Referenced:**  
- [[Technologies/]]

**Solutions Applied:**  
- [[Solutions/]]

**Related Projects:**  
- [[Projects/]]

## Related Meetings
`$= dv.table(["Meeting", "Date", "Type"], dv.pages('"Meetings"').where(p => p.file.name !== dv.current().file.name && (p.project === dv.current().project || p.tags?.some(t => dv.current().tags?.includes(t)))).sort(p => p.date, 'desc').limit(5).map(p => [p.file.link, p.date, p.meeting_type]))`

## Meeting Quality
**Effectiveness:** High / Medium / Low  
**Decision Quality:** Good / Fair / Poor  
**Action Clarity:** Clear / Unclear  
**Follow-up Needed:** Yes / No  

## Meeting Notes
<!-- Main discussion points and detailed notes go here -->

### Discussion Points
1. 

### Key Takeaways
- 

### Raw Notes
<!-- Unstructured notes taken during the meeting -->

## Transcript
<!-- If auto-generated, the full transcript will appear here -->

---
## Metadata
**Created:** {{date}} {{time}}  
**Last Modified:** {{date}} {{time}}  
**Template Version:** 2.0