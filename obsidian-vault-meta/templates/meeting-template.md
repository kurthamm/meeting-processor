---

## type: meeting date: time: meeting-type: project: status: processed duration: attendees-internal: attendees-external: key-decision-makers: meeting-outcome: energy-level: follow-up-required: tags: meeting

# Meeting Title

## Meeting Information

**Type:** Meeting  
**Date:** **Time:** **Project:** **Meeting Type:** Technical Review / Sales Call / Planning / Standup / Demo / Crisis  
**Duration:** **Status:** Processed

## Attendees

**Internal Team:** **Client/External:** **Key Decision Makers:**

## Meeting Context

**Purpose:** **Agenda Items:** **Background:** **Expected Outcomes:**

## Meeting Quality Indicators

**Energy Level:** High / Medium / Low  
**Meeting Outcome:** Successful / Needs-Follow-up / Blocked  
**Effectiveness:** High / Medium / Low  
**Decision Quality:** Good / Fair / Poor  
**Action Clarity:** Clear / Unclear  
**Follow-up Needed:** Yes / No

## Key Decisions Made

<!-- Extracted automatically and manually added -->

## Action Items

<!-- Links to task records will be populated here -->

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
SORT priority DESC, due_date ASC
```

## Technical Discussions

**Architecture Decisions:** **Technology Choices:** **Integration Approaches:** **Performance Considerations:**

## Issues Identified

**Blockers:** **Technical Challenges:** **Business Risks:** **Dependencies:**

## Opportunities Discovered

**Upsell Potential:** **Future Projects:** **New Requirements:** **Partnership Options:**

## Knowledge Captured

**New Insights:** **Best Practices:** **Lessons Learned:** **Process Improvements:**

## Follow-up Required

**Next Meeting:** **Documentation Needed:** **Research Tasks:** **Client Communication:**

### Follow-up Meetings

```dataview
list
from "Meetings"
where contains(file.text, this.file.name) or contains(follow-up-required, this.file.link)
where file.name != this.file.name
sort date desc
```

## Entity Connections

**People Mentioned:** **Companies Discussed:** **Technologies Referenced:** **Solutions Applied:** **Related Projects:**

### People in This Meeting

```dataview
LIST
FROM "People"
WHERE contains(file.inlinks, this.file.link)
```

### Companies Discussed

```dataview
LIST
FROM "Companies"
WHERE contains(file.inlinks, this.file.link)
```

### Technologies Referenced

```dataview
LIST
FROM "Technologies"
WHERE contains(file.inlinks, this.file.link)
```

## Related Meetings

```dataview
table without id
  file.link as "Meeting",
  date as "Date",
  meeting-type as "Type"
from "Meetings"
where (contains(project, this.project) or any(file.etags, (t) => contains(this.file.etags, t)))
where file.name != this.file.name
sort date desc
limit 5
```

## Meeting Analytics

```dataview
TABLE WITHOUT ID
  "Meeting Metrics" as Metric,
  choice(length(filter(file.tasks, (t) => t.completed = false)), length(filter(file.tasks, (t) => t.completed = false)), "0") as "Open Tasks",
  choice(length(filter(file.tasks, (t) => t.completed = true)), length(filter(file.tasks, (t) => t.completed = true)), "0") as "Completed Tasks",
  choice(length(file.outlinks), length(file.outlinks), "0") as "Connections"
WHERE file.path = this.file.path
```

## Complete Transcript

<!-- Full transcript will be inserted here by the Meeting Processor -->

---

**Tags:** #meeting #project/active #type/technical-review  
**Audio File:** **Processed:** **Auto-generated:** Yes  
**Confidence Level:** High / Medium / Low

## Template Usage Notes

<!-- This template is designed for use with the Meeting Processor system. All fields will be automatically populated when processing meeting recordings. For manual meeting notes, simply fill in the fields above. YAML Frontmatter Fields: - type: Always "meeting" for Dataview queries - date: Meeting date (YYYY-MM-DD format) - time: Meeting time (HH:mm format) - meeting-type: Category of meeting - project: Project association - status: Processing status - meeting-outcome: Success indicator - energy-level: Meeting energy/engagement - follow-up-required: Boolean for follow-ups -->