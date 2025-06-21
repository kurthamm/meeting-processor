# 📋 Task Management Dashboard

_Last Updated: <%tp.date.now("YYYY-MM-DD HH:mm")%>_

## 📊 Task Overview

```dataview
TABLE WITHOUT ID
  choice(sum(rows.file.link), "**" + sum(rows.file.link) + "** Total Tasks", "**0** Total Tasks") as "Total Tasks",
  choice(sum(rows.New), "**" + sum(rows.New) + "** New", "**0** New") as "New",
  choice(sum(rows.InProgress), "**" + sum(rows.InProgress) + "** In Progress", "**0** In Progress") as "In Progress",
  choice(sum(rows.Done), "**" + sum(rows.Done) + "** Done", "**0** Done") as "Done"
FROM "Tasks"
WHERE file.name != this.file.name
GROUP BY true
FLATTEN length(filter(rows.file, (f) => f.frontmatter.status = "new" OR !f.frontmatter.status)) as New
FLATTEN length(filter(rows.file, (f) => f.frontmatter.status = "in_progress")) as InProgress
FLATTEN length(filter(rows.file, (f) => f.frontmatter.status = "done")) as Done
LIMIT 1
```

## 🚨 Urgent & Overdue Tasks

### ⏰ Overdue Tasks

```dataview
TASK
FROM "Tasks"
WHERE !completed AND due_date < date(today)
WHERE file.name != this.file.name
SORT due_date ASC
LIMIT 20
```

_No overdue tasks found_ <!-- This text shows when query returns empty -->

### 🔥 High Priority Tasks

```dataview
TASK
FROM "Tasks"
WHERE !completed AND priority = "high"
WHERE file.name != this.file.name
SORT due_date ASC
LIMIT 15
```

_No high priority tasks found_ <!-- This text shows when query returns empty -->

### 🚨 Critical Priority Tasks

```dataview
TASK
FROM "Tasks"
WHERE !completed AND priority = "critical"
WHERE file.name != this.file.name
SORT due_date ASC
LIMIT 10
```

_No critical tasks found_ <!-- This text shows when query returns empty -->

## 📈 Task Board by Status

### 🆕 New Tasks

```dataview
TABLE WITHOUT ID
  link(file.link, default(title, file.name)) as "Task",
  default(priority, "medium") as "Priority",
  default(assigned_to, "unassigned") as "Assigned To",
  default(due_date, "not set") as "Due Date"
FROM "Tasks"
WHERE (status = "new" OR !status) AND file.name != this.file.name
SORT priority DESC, due_date ASC
LIMIT 25
```

_No new tasks_ <!-- Fallback message -->

### 📋 Ready for Work

```dataview
TABLE WITHOUT ID
  link(file.link, default(title, file.name)) as "Task",
  default(priority, "medium") as "Priority",
  default(assigned_to, "unassigned") as "Assigned To",
  default(due_date, "not set") as "Due Date"
FROM "Tasks"
WHERE status = "ready" AND file.name != this.file.name
SORT priority DESC, due_date ASC
LIMIT 20
```

_No tasks ready for work_ <!-- Fallback message -->

### 🚀 In Progress

```dataview
TABLE WITHOUT ID
  link(file.link, default(title, file.name)) as "Task",
  default(priority, "medium") as "Priority",
  default(assigned_to, "unassigned") as "Assigned To",
  default(due_date, "not set") as "Due Date"
FROM "Tasks"
WHERE status = "in_progress" AND file.name != this.file.name
SORT assigned_to ASC, priority DESC
LIMIT 20
```

_No tasks in progress_ <!-- Fallback message -->

### 🔍 In Review

```dataview
TABLE WITHOUT ID
  link(file.link, default(title, file.name)) as "Task",
  default(priority, "medium") as "Priority",
  default(assigned_to, "unassigned") as "Reviewer",
  default(due_date, "not set") as "Due Date"
FROM "Tasks"
WHERE status = "in_review" AND file.name != this.file.name
SORT priority DESC, due_date ASC
LIMIT 15
```

_No tasks in review_ <!-- Fallback message -->

### 🚫 Blocked Tasks

```dataview
TABLE WITHOUT ID
  link(file.link, default(title, file.name)) as "Task",
  default(priority, "medium") as "Priority",
  default(assigned_to, "unassigned") as "Assigned To",
  default(blocked_reason, "not specified") as "Blocked Reason"
FROM "Tasks"
WHERE status = "blocked" AND file.name != this.file.name
SORT priority DESC
LIMIT 15
```

_No blocked tasks_ <!-- Fallback message -->

### ✅ Recently Completed (Last 7 Days)

```dataview
TABLE WITHOUT ID
  link(file.link, default(title, file.name)) as "Task",
  default(assigned_to, "unassigned") as "Completed By",
  default(completed_date, "unknown") as "Completed Date"
FROM "Tasks"
WHERE status = "done" AND file.name != this.file.name
WHERE completed_date >= date(today) - dur(7 days)
SORT completed_date DESC
LIMIT 20
```

_No recently completed tasks_ <!-- Fallback message -->

## 👥 Team Workload

### Active Tasks by Person

```dataview
TABLE WITHOUT ID
  assigned_to as "Team Member",
  length(rows) as "Total Tasks",
  length(filter(rows, (r) => r.priority = "critical")) as "Critical",
  length(filter(rows, (r) => r.priority = "high")) as "High",
  length(filter(rows, (r) => r.status = "in_progress")) as "In Progress"
FROM "Tasks"
WHERE status != "done" AND status != "cancelled" AND assigned_to != null AND assigned_to != "" AND assigned_to != "unassigned"
WHERE file.name != this.file.name
GROUP BY assigned_to
SORT length(rows) DESC
LIMIT 20
```

_No assigned tasks found_ <!-- Fallback message -->

### Unassigned High Priority Tasks

```dataview
LIST
FROM "Tasks"
WHERE (assigned_to = null OR assigned_to = "" OR assigned_to = "unassigned")
AND (priority = "high" OR priority = "critical")
AND status != "done" AND status != "cancelled"
WHERE file.name != this.file.name
SORT priority DESC, due_date ASC
LIMIT 10
```

_No unassigned high priority tasks_ <!-- Fallback message -->

## 📊 Sprint Metrics

### Current Sprint Tasks

```dataview
TABLE WITHOUT ID
  default(category, "general") as "Category",
  length(rows) as "Count",
  length(filter(rows, (r) => r.status = "done")) as "Completed",
  length(filter(rows, (r) => r.status = "in_progress")) as "In Progress",
  length(filter(rows, (r) => r.status = "new" OR !r.status)) as "Not Started"
FROM "Tasks"
WHERE contains(sprint, dateformat(date(today), "yyyy-'W'WW")) OR !sprint
WHERE file.name != this.file.name
GROUP BY category
SORT length(rows) DESC
LIMIT 10
```

_No sprint data available_ <!-- Fallback message -->

## 📈 Priority Distribution

```dataview
TABLE WITHOUT ID
  default(priority, "medium") as "Priority",
  length(rows) as "Total",
  length(filter(rows, (r) => r.status != "done" AND r.status != "cancelled")) as "Active",
  length(filter(rows, (r) => r.status = "done")) as "Completed"
FROM "Tasks"
WHERE file.name != this.file.name
GROUP BY priority
SORT 
  choice(priority = "critical", 1,
  choice(priority = "high", 2,
  choice(priority = "medium", 3, 4))) ASC
LIMIT 10
```

## 📅 Upcoming Deadlines (Next 14 Days)

```dataview
TABLE WITHOUT ID
  link(file.link, default(title, file.name)) as "Task",
  default(priority, "medium") as "Priority",
  default(assigned_to, "unassigned") as "Assigned To",
  due_date as "Due Date",
  (date(today) - due_date).days as "Days Until Due"
FROM "Tasks"
WHERE due_date != null 
  AND due_date >= date(today) 
  AND due_date <= date(today) + dur(14 days)
  AND status != "done" 
  AND status != "cancelled"
WHERE file.name != this.file.name
SORT due_date ASC
LIMIT 20
```

_No upcoming deadlines in the next 14 days_ <!-- Fallback message -->

## 🔄 Task Flow Metrics (Last 30 Days)

### Tasks Created vs Completed

```dataview
TABLE WITHOUT ID
  "Last 30 Days" as Period,
  length(filter(rows, (r) => r.created >= date(today) - dur(30 days))) as "Created",
  length(filter(rows, (r) => r.status = "done" AND r.completed_date >= date(today) - dur(30 days))) as "Completed",
  length(filter(rows, (r) => r.status = "cancelled" AND r.modified >= date(today) - dur(30 days))) as "Cancelled"
FROM "Tasks"
WHERE file.name != this.file.name
GROUP BY true
LIMIT 1
```

## 🏷️ Tasks by Category

```dataview
TABLE WITHOUT ID
  default(category, "uncategorized") as "Category",
  length(rows) as "Total",
  length(filter(rows, (r) => r.status = "in_progress")) as "Active",
  length(filter(rows, (r) => r.priority = "high" OR r.priority = "critical")) as "High Priority"
FROM "Tasks"
WHERE status != "done" AND status != "cancelled"
WHERE file.name != this.file.name
GROUP BY category
SORT length(rows) DESC
LIMIT 15
```

_No categorized tasks found_ <!-- Fallback message -->

## 🔍 Quick Filters

### My Tasks

[[Tasks#My Active Tasks|View My Tasks]] | [[Tasks#My Completed Tasks|View My Completed]]

### By Priority

[[Tasks#Critical|Critical]] | [[Tasks#High|High Priority]] | [[Tasks#Medium|Medium Priority]] | [[Tasks#Low|Low Priority]]

### By Status

[[Tasks#New|New]] | [[Tasks#Ready|Ready]] | [[Tasks#InProgress|In Progress]] | [[Tasks#Review|In Review]] | [[Tasks#Blocked|Blocked]] | [[Tasks#Done|Completed]]

---

## 📝 Dashboard Notes

This dashboard automatically updates based on your task data. All queries include error handling and fallback messages for when no data is available.

**Key Features:**

- Error-resistant queries with `default()` functions
- Fallback messages for empty results
- Query limits to prevent performance issues
- Smart sorting for most relevant results first
- Null-safe operations throughout

**Last Dashboard Update:** <%tp.date.now("YYYY-MM-DD HH:mm")%> **Auto-refresh:** This dashboard uses live Dataview queries

---

_Tags:_ #dashboard #tasks #project-management