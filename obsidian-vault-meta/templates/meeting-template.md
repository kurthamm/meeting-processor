# {{title}}

Date: {{date}}
Type: {{meeting_type}}
Duration: {{duration}}
Project: {{project}}

## Attendees
{{attendees}}

## Action Items
<!-- Auto-populated with task links by meeting processor -->

### All Tasks from This Meeting
```dataview
TABLE WITHOUT ID
  file.link as Task,
  status as Status,
  priority as Priority,
  assigned_to as "Assigned To",
  due_date as "Due Date"
FROM "Tasks"
WHERE meeting_source = this.file.name OR contains(meeting_source, this.file.name)
SORT 
  choice(priority = "critical", 1, priority = "high", 2, priority = "medium", 3, priority = "low", 4) ASC,
  due_date ASC
```

## Key Decisions
<!-- Key decisions made during this meeting -->

## Summary
<!-- Meeting summary and key points -->

## Next Steps
<!-- Follow-up actions and next meeting plans -->

## Entity Connections
**People:** 
**Companies:** 
**Technologies:** 

## Related Meetings
```dataview
TABLE WITHOUT ID
  file.link as "Meeting",
  date as "Date",
  type as "Type"
FROM "Meetings"
WHERE project = this.project AND file.name != this.file.name
SORT date DESC
LIMIT 5
```

---
**Tags:** #meeting #{{meeting_type}}
**Processed:** {{processed_date}}