# {{name}}

**Company:** {{company}}
**Role:** {{role}}
**Email:** {{email}}
**Last Contact:** {{date}}

## About
<!-- AI-generated context about this person -->

## Active Tasks
```dataview
TABLE WITHOUT ID
  file.link as Task,
  status as Status,
  priority as Priority,
  due_date as "Due Date"
FROM "Tasks"
WHERE assigned_to = this.file.name OR contains(assigned_to, "{{name}}")
WHERE status != "done" AND status != "cancelled"
SORT priority DESC
```

## Meeting History
```dataview
TABLE WITHOUT ID 
  file.link as "Meeting",
  date as "Date",
  type as "Type"
FROM "Meetings"
WHERE contains(file.outlinks, this.file.link)
SORT date DESC
LIMIT 10
```

## Notes
<!-- Additional context and observations -->

---
**Tags:** #person #contact
**Created:** {{date}}