---
status: new
priority: medium
category: 
assigned_to: 
due_date: 
meeting_source: 
sprint: 
story_points: 
---

# {{title}}

## Task Overview
**Status:** 🆕 New  
**Priority:** ⚡ Medium  
**Category:** {{category}}  
**Sprint:** {{sprint}}  
**Story Points:** {{points}}  

## Assignment
**Assigned To:** {{assigned_to}}  
**Due Date:** {{due_date}}  
**Source:** [[Meetings/{{meeting}}|📝 Meeting Notes]]  
**Dashboard:** [[Meta/dashboards/Task-Dashboard|📊 Sprint Board]]  

## Description
*What needs to be done?*

## Acceptance Criteria
*Definition of done - what makes this task complete?*

- [ ] 
- [ ] 
- [ ] 

## Context & Background
*Why does this task exist? What problem does it solve?*

## Technical Details
*Implementation notes, approach, considerations*

## Dependencies
**Blocked By:**  
**Blocks:**  
**Related Tasks:**  

## Progress Tracking
- [ ] Task refined and ready
- [ ] Development started
- [ ] Implementation complete
- [ ] Code review passed
- [ ] Testing complete
- [ ] Documentation updated
- [ ] Deployed/Released

## Work Log
*Track progress and time spent*

### {{date}} - Status Update
- Status changed from `new` to `ready`
- Assigned to: 
- Notes: 

## Testing Notes
*How to verify this task is complete*

## Related Information
**Documentation:**  
**Design Docs:**  
**Related PRs:**  

## Sprint Retrospective
*What went well? What could improve?*

---

### Related Tasks
```dataview
TABLE WITHOUT ID
  file.link as "Task",
  status as "Status",
  priority as "Priority",
  assigned_to as "Owner"
FROM "Tasks"
WHERE contains(file.outlinks, this.file.link) OR contains(this.file.outlinks, file.link)
WHERE file.path != this.file.path
SORT priority DESC
```

### From Same Meeting
```dataview
LIST
FROM "Tasks"
WHERE meeting_source = this.meeting_source
WHERE file.path != this.file.path
SORT priority DESC
```

---

**Tags:** #task #status/new #{{category}}  
**Created:** {{date}}  
**Modified:** {{date}}  
**Task ID:** `{{task_id}}`