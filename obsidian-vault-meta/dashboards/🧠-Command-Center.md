# 🧠 Command Center

**Last Updated:** {{date}}
**User:** {{user}}

## 📊 Overview

```dataview
TABLE WITHOUT ID
  "📅 " + length(filter(rows, (r) => contains(r.file.path, "Meetings/"))) as Meetings,
  "📋 " + length(filter(rows, (r) => contains(r.file.path, "Tasks/"))) as Tasks,
  "👥 " + length(filter(rows, (r) => contains(r.file.path, "People/"))) as People,
  "🏢 " + length(filter(rows, (r) => contains(r.file.path, "Companies/"))) as Companies,
  "💻 " + length(filter(rows, (r) => contains(r.file.path, "Technologies/"))) as Technologies
FROM ""
WHERE file.path != this.file.path
```

## 🚨 Urgent Attention

### Overdue Tasks
```dataview
TABLE WITHOUT ID
  file.link as Task,
  priority as Priority,
  assigned_to as "Owner",
  due_date as "Due Date"
FROM "Tasks"
WHERE due_date < date(today) AND status != "done" AND status != "cancelled" AND due_date != ""
SORT priority DESC, due_date ASC
LIMIT 5
```

### Critical Priority Tasks
```dataview
TABLE WITHOUT ID
  file.link as Task,
  status as Status,
  assigned_to as "Owner"
FROM "Tasks"
WHERE priority = "critical" AND status != "done"
SORT status ASC
```

## 📅 Recent Activity

### This Week's Meetings
```dataview
TABLE WITHOUT ID
  file.link as Meeting,
  date as Date,
  choice(length(filter(file.outlinks, (l) => contains(string(l), "Tasks/"))), 0, "No tasks", 1, "1 task", length(filter(file.outlinks, (l) => contains(string(l), "Tasks/"))) + " tasks") as Tasks
FROM "Meetings"
WHERE date >= date(today) - dur(7 days)
SORT date DESC
```

### Active Tasks by Status
```dataview
TABLE WITHOUT ID
  "🆕 New: " + length(filter(rows, (r) => r.status = "new")) as New,
  "📋 Ready: " + length(filter(rows, (r) => r.status = "ready")) as Ready,
  "🚀 In Progress: " + length(filter(rows, (r) => r.status = "in_progress")) as Active,
  "🚫 Blocked: " + length(filter(rows, (r) => r.status = "blocked")) as Blocked
FROM "Tasks"
WHERE status != "done" AND status != "cancelled"
```

## 🏢 Key Relationships

### Active Companies
```dataview
TABLE WITHOUT ID
  file.link as Company,
  choice(contains(string(file.content), "Client"), "🤝 Client", contains(string(file.content), "Partner"), "🤝 Partner", contains(string(file.content), "Vendor"), "📦 Vendor", "🔍 Prospect") as Relationship,
  length(filter(file.inlinks, (l) => contains(string(l), "Meetings/"))) as Meetings
FROM "Companies"
WHERE file.mtime >= date(today) - dur(30 days)
SORT file.mtime DESC
LIMIT 5
```

### Recent Contacts
```dataview
TABLE WITHOUT ID
  file.link as Person,
  company as Company,
  choice(length(filter(file.inlinks, (l) => contains(string(l), "Tasks/"))), 0, "", length(filter(file.inlinks, (l) => contains(string(l), "Tasks/"))) + " tasks") as Tasks
FROM "People"
WHERE file.mtime >= date(today) - dur(14 days)
SORT file.mtime DESC
LIMIT 5
```

## 📈 Productivity Insights

### Task Velocity (Last 7 Days)
```dataview
TABLE WITHOUT ID
  "✅ Completed: " + length(filter(rows, (r) => r.status = "done" AND r.file.mtime >= date(today) - dur(7 days))) as Completed,
  "🆕 Created: " + length(filter(rows, (r) => r.created >= date(today) - dur(7 days))) as Created,
  "📊 Net: " + (length(filter(rows, (r) => r.created >= date(today) - dur(7 days))) - length(filter(rows, (r) => r.status = "done" AND r.file.mtime >= date(today) - dur(7 days)))) as Net
FROM "Tasks"
```

### Meeting Frequency
```dataview
TABLE WITHOUT ID
  "This Week: " + length(filter(rows, (r) => r.date >= date(today) - dur(7 days))) as "This Week",
  "Last Week: " + length(filter(rows, (r) => r.date >= date(today) - dur(14 days) AND r.date < date(today) - dur(7 days))) as "Last Week",
  "This Month: " + length(filter(rows, (r) => r.date >= date(today) - dur(30 days))) as "This Month"
FROM "Meetings"
```

## 🎯 Quick Actions

### Navigate
- [[Meta/dashboards/Task-Dashboard|📊 Task Board]]
- [[Tasks/|📋 All Tasks]]
- [[Meetings/|📅 All Meetings]]
- [[People/|👥 All Contacts]]

### Create New
- [[Templates/task-template|➕ New Task]]
- [[Templates/meeting-template|➕ New Meeting]]
- [[Templates/person-template|➕ New Contact]]

---

*Auto-refreshing dashboard powered by Dataview*  
**Generated:** {{date}}