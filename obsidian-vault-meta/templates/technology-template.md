# {{technology_name}}

**Category:** {{category}}
**Status:** {{status}}
**Owner:** {{owner}}

## Overview
<!-- AI-generated technology context -->

## Current Usage
<!-- How we're using this technology -->

## Related Tasks
```dataview
TABLE WITHOUT ID
  file.link as Task,
  status as Status,
  priority as Priority
FROM "Tasks"
WHERE contains(file.content, "{{technology_name}}")
WHERE status != "done"
SORT priority DESC
```

## Implementation History
```dataview
TABLE WITHOUT ID
  file.link as "Meeting",
  date as "Date"
FROM "Meetings"
WHERE contains(file.outlinks, this.file.link)
SORT date DESC
LIMIT 10
```

---
**Tags:** #technology #{{category}}
**Created:** {{date}}