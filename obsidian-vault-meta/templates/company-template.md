# {{company_name}}

**Industry:** {{industry}}
**Relationship:** {{relationship}}
**Status:** {{status}}
**Website:** {{website}}

## Overview
<!-- AI-generated company context -->

## Key Contacts
```dataview
TABLE WITHOUT ID
  file.link as "Person",
  role as "Role",
  email as "Email"
FROM "People"
WHERE company = "{{company_name}}"
SORT role ASC
```

## Active Projects & Tasks
```dataview
TABLE WITHOUT ID
  file.link as Task,
  status as Status,
  priority as Priority,
  due_date as "Due Date"
FROM "Tasks"
WHERE contains(file.content, "{{company_name}}")
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

## Technologies Used
```dataview
LIST
FROM "Technologies"
WHERE contains(file.inlinks, this.file.link)
```

---
**Tags:** #company #{{relationship}}
**Created:** {{date}}