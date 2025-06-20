🎙️ Meeting Processor
An AI-powered meeting transcription and knowledge management system that transforms your recordings into structured, searchable knowledge in Obsidian with comprehensive Agile/Scrum task management and intelligent dashboards.
🚀 What It Does
Drop an MP4 → Get Complete Knowledge Management + Agile Task Tracking

🗄️ Auto-ingests MP4 recordings from a watched folder
🔊 Converts to optimized FLAC audio with smart chunking for large files
🤖 Transcribes with OpenAI Whisper (handles files of any size)
🧠 Analyzes with Anthropic Claude for summaries, decisions, and action items
🎭 Identifies speakers and formats conversations naturally
🔍 Detects entities (people, companies, technologies) with AI context
📋 Extracts ALL tasks following Agile/Scrum methodology
🏗️ Creates smart notes in Obsidian with contextual entity relationships
📊 Generates dashboards with real-time Dataview queries
🔗 Builds knowledge graphs with bi-directional linking

✨ Key Features
🏃 Agile/Scrum Task Management

Industry-Standard Workflow: Tasks flow through new → ready → in_progress → in_review → done
YAML Frontmatter: All tasks use Dataview-compatible frontmatter for powerful queries
Sprint Tracking: Monitor velocity, team workload, and sprint metrics
Priority System: critical, high, medium, low with visual indicators
Category Classification: technical, business, process, documentation, research
Unified Dashboard: Real-time task board with Dataview queries

🧠 AI-Powered Intelligence

Smart Entity Detection: Automatically identifies people, companies, and technologies
Contextual Understanding: Uses your company context to determine relationships
Rich Entity Profiles: Creates detailed notes with contact info, project involvement, and meeting history
Knowledge Graph Building: Links people to companies, technologies to projects, meetings to decisions

📊 Dashboard System

🧠 Command Center: Main overview with live Dataview queries
📋 Task Dashboard: Comprehensive task management with sprint metrics
Real-time Updates: All dashboards use Dataview for live data
Custom Templates: Full template system for consistent note creation

📁 What's Included
Obsidian Templates & Configuration

Meeting Template: Structured format with all metadata fields
Task Template: YAML frontmatter with Agile workflow states
Person/Company/Technology Templates: Entity relationship tracking
Dashboard Templates: Command Center and Task Dashboard with Dataview
Plugin Configurations: Dataview queries and Templater settings

Core Processing Pipeline

Audio processing with FFmpeg (MP4 → FLAC)
OpenAI Whisper transcription with chunking
Claude AI analysis and speaker identification
Entity detection and relationship mapping
Task extraction with priority and assignment
Obsidian note generation with cross-linking

🛠️ Quick Start
1. Clone & Setup
bashgit clone https://github.com/kurthamm/meeting-processor.git
cd meeting-processor
cp .env.sample .env
2. Configure Environment
Edit .env with your settings:
env# API Keys (Required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...

# Obsidian Integration
OBSIDIAN_VAULT_PATH=C:/Obsidian_Vaults/My_Vault
OBSIDIAN_FOLDER_PATH=Meetings

# Company Context (Optional but recommended)
OBSIDIAN_COMPANY_NAME=YourCompany
OBSIDIAN_USER_NAME=YourName
3. Set Up Obsidian
Install Required Plugins

Dataview - For dynamic queries and dashboards
Templater - For template functionality (optional)

Copy Templates to Your Vault
bash# Copy the entire Meta folder structure
cp -r obsidian-vault-meta/* /path/to/your/vault/Meta/

# Copy plugin configurations
cp -r obsidian-vault-plugins/dataview/* /path/to/your/vault/.obsidian/plugins/dataview/
Create Required Folders
Your vault should have this structure:
Your_Vault/
├── Meetings/          # Meeting notes go here
├── Tasks/             # Individual task files
├── People/            # Person profiles
├── Companies/         # Company profiles
├── Technologies/      # Technology documentation
└── Meta/
    ├── dashboards/    # Dashboard files
    │   ├── 🧠-Command-Center.md
    │   └── Task-Dashboard.md
    └── templates/     # Note templates
        ├── meeting-template.md
        ├── task-template.md
        ├── person-template.md
        ├── company-template.md
        └── technology-template.md
4. Build & Run
bash# Using Docker Compose
docker-compose up --build -d

# Or using the PowerShell script (Windows)
.\rebuild.ps1 rebuild
5. Process Your First Meeting

Drop an MP4 file into the input/ directory
Watch the logs: docker logs -f meeting-processor
Find your processed meeting in Obsidian
Check the dashboards for updated intelligence

📊 Dashboard Features
🧠 Command Center Dashboard

Quick Stats: Total meetings, tasks, people, companies, technologies
Urgent Tasks: Overdue and high-priority items
Recent Activity: Latest meetings and interactions
AI Insights: Pattern detection and recommendations
Live Dataview Queries: Real-time data from your vault

📋 Task Dashboard

Sprint Overview: Current sprint status and velocity
Task Board: Kanban-style view by status
Priority Matrix: Tasks by priority and assignment
Team Workload: Tasks per person
Overdue Alerts: Tasks past their due date

🎯 Complete Workflow Example
1. Drop Recording
input/client-strategy-meeting.mp4
2. Automatic Processing
🎵 Converting to FLAC...
🎤 Transcribing with Whisper...
🧠 Analyzing with Claude...
🔍 Detecting entities: Madison, PSA, Salesforce, Lambda
📋 Extracting 7 tasks from meeting...
🏗️ Creating entity notes with AI context...
📝 Generating meeting note with task links...
📊 Updating dashboards...
✅ Complete!
3. Generated Knowledge System

Meeting Note: Structured note with analysis and transcript
Task Records: Individual task files with YAML frontmatter
Entity Notes: People, companies, and technologies mentioned
Updated Dashboards: Real-time view of all activity

🔧 Advanced Configuration
Custom Task Priorities
Edit config/settings.py to add custom priorities:
pythonTASK_PRIORITIES = ['critical', 'high', 'medium', 'low', 'backlog']
PRIORITY_EMOJIS = {
    'critical': '🚨',
    'high': '🔥',
    'medium': '⚡',
    'low': '📌',
    'backlog': '📦'
}
Custom Categories
Add domain-specific categories:
pythonTASK_CATEGORIES = ['technical', 'business', 'process', 'documentation', 'research', 'your-category']
Dashboard Customization
Edit the Dataview queries in:

obsidian-vault-meta/dashboards/🧠-Command-Center.md
obsidian-vault-meta/dashboards/Task-Dashboard.md

📋 Template System
Meeting Template Features

Structured sections for all meeting aspects
Dataview queries for related content
Automatic task aggregation
Entity relationship tracking

Task Template Features

Complete YAML frontmatter
Agile workflow states
Priority and category system
Progress tracking
Work log sections

Entity Templates

People: Role, company, expertise, meeting history
Companies: Relationship status, contacts, technologies
Technologies: Implementation status, business value, usage

🤝 Contributing
Contributions are welcome! Areas for enhancement:

Integrations: Jira, Azure DevOps, Slack
Analytics: Advanced metrics and reporting
AI Features: Better entity detection, task estimation
Workflow: Custom task states and automations

Development Setup

Fork the repository
Create a feature branch
Make your changes
Test with sample recordings
Submit a PR

📜 License
MIT License - Use freely with attribution
🎯 Perfect For

Agile Teams: Sprint planning and retrospectives
Consultants: Client meeting documentation
Project Managers: Comprehensive task tracking
Sales Teams: CRM integration and follow-ups
Anyone: Who wants to never miss an action item again

🙏 Acknowledgments
Built with:

OpenAI Whisper for transcription
Anthropic Claude for analysis
Obsidian for knowledge management
Dataview for dynamic queries


Transform your meetings into actionable intelligence with AI-powered automation.
Never lose track of a decision, task, or important discussion again.