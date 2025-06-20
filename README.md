# 🎙️ Meeting Processor

An **AI-powered, modular** meeting transcription and knowledge management system that transforms your recordings into structured, searchable knowledge in Obsidian.

## 🚀 What It Does

**Drop an MP4 → Get Intelligent Knowledge Management**

* 🗄️ **Auto-ingests** MP4 recordings from a watched folder
* 🔊 **Converts** to optimized FLAC audio with smart chunking
* 🤖 **Transcribes** with OpenAI Whisper (handles files of any size)
* 🧠 **Analyzes** with Anthropic Claude for summaries, decisions, and action items
* 🎭 **Identifies speakers** and formats conversations naturally
* 🔍 **Detects entities** (people, companies, technologies) with AI
* 🏗️ **Creates smart notes** in Obsidian with contextual entity relationships
* 📝 **Generates structured templates** for meetings, people, companies, and technologies
* 🔗 **Builds knowledge graphs** with bi-directional linking between all entities

---

## ✨ Key Features

### 🧠 **AI-Powered Entity Intelligence**
- **Smart Entity Detection**: Automatically identifies people, companies, and technologies mentioned
- **Contextual Understanding**: Uses your company context to determine relationships (colleague vs. client)
- **Rich Entity Profiles**: Creates detailed notes with contact info, project involvement, and meeting history
- **Knowledge Graph Building**: Links people to companies, technologies to projects, meetings to decisions

### 📊 **Professional Meeting Notes**
- **Executive Summaries**: Key decisions, action items, and next steps
- **Speaker Identification**: Natural conversation flow with speaker labels
- **Technical Documentation**: Architecture decisions, technology choices, integration approaches
- **Business Intelligence**: Opportunities, risks, and relationship insights

### 🔄 **Modular Architecture**
- **Clean Separation**: Audio processing, transcription, analysis, and entity management
- **Easy Maintenance**: Focused modules for each responsibility
- **Extensible Design**: Add new entity types or analysis features easily
- **Robust Error Handling**: Graceful degradation and detailed logging

### 🏢 **Business Context Awareness**
- **Company Recognition**: Knows your employer from Obsidian vault
- **Relationship Mapping**: Client vs. vendor vs. colleague detection
- **Project Tracking**: Links technologies to implementations and business value
- **Decision History**: Tracks technical and business decisions over time

---

## 📋 Prerequisites

* **Docker & Docker Compose** installed
* **API Keys** for:
  * [OpenAI Platform](https://platform.openai.com/) (for Whisper transcription)
  * [Anthropic Console](https://console.anthropic.com/) (for Claude analysis)
* **Obsidian Vault** (local path for direct integration)

---

## 🛠️ Quick Start

### 1. **Clone & Setup**
```bash
git clone https://github.com/YourUser/meeting-processor.git
cd meeting-processor
cp .env.sample .env
```

### 2. **Configure Environment**
Edit `.env` with your settings:
```env
# API Keys (Required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...

# Obsidian Integration
OBSIDIAN_VAULT_PATH=C:/Obsidian_Vaults/My_Vault
OBSIDIAN_FOLDER_PATH=Meetings

# Docker Paths
INPUT_DIR=/app/input
OUTPUT_DIR=/app/output
PROCESSED_DIR=/app/processed

# Testing & Development
TESTING_MODE=true
```

### 3. **Build & Run**
```bash
# Using the enhanced PowerShell script
.\rebuild.ps1 rebuild

# Or traditional Docker Compose
docker-compose up --build -d
```

### 4. **Setup Your Company Context**
Create a company note in Obsidian at `/Companies/Your-Company.md`:
```markdown
# Your Company Name

**Current Employer:** Yes

## Company Information
Industry: Your Industry
Location: Your Location
```

---

## 📂 Modern Architecture

```
meeting-processor/
├── main.py                    # Application entry point
├── config/                    # Configuration management
│   ├── settings.py           # Environment & API setup
├── core/                     # Core processing
│   ├── audio_processor.py    # MP4→FLAC conversion & chunking
│   ├── transcription.py      # OpenAI Whisper integration
│   ├── claude_analyzer.py    # AI analysis & speaker ID
│   └── file_manager.py       # File operations & tracking
├── entities/                 # Smart entity management
│   ├── detector.py          # AI entity detection
│   ├── manager.py           # Obsidian note creation
│   └── ai_context.py        # Context extraction
├── obsidian/                # Obsidian integration
│   └── formatter.py         # Note templates & formatting
├── monitoring/              # File system monitoring
│   └── file_watcher.py      # MP4 detection & processing
└── utils/                   # Shared utilities
    └── logger.py            # Enhanced logging
```

---

## 🎯 Workflow Example

**1. Drop Recording** → `input/client-meeting.mp4`

**2. AI Processing**
```
🎵 Converting to FLAC...
🎤 Transcribing with Whisper...
🧠 Analyzing with Claude...
🔍 Detecting entities: Madison, PSA, Salesforce
🏗️ Creating entity notes with context...
📝 Generating meeting note...
✅ Complete!
```

**3. Generated Knowledge**
- **Meeting Note**: `Client-Strategy-Call_2025-06-20_14-30_meeting.md`
- **Person Note**: `People/Madison.md` (with role, company, relationship)
- **Company Note**: `Companies/PSA.md` (with business needs, relationship status)
- **Technology Note**: `Technologies/Salesforce.md` (with implementation details)

**4. Obsidian Integration**
- All notes linked bi-directionally
- Entity relationships mapped
- Meeting history tracked
- Knowledge graph automatically built

---

## 🔧 Management Commands

```bash
# Quick restart after code changes
.\rebuild.ps1 restart

# Full rebuild after dependency changes
.\rebuild.ps1 rebuild

# View live logs
.\rebuild.ps1 logs

# Check container status
.\rebuild.ps1 status

# Clean rebuild (if Docker issues)
.\rebuild.ps1 clean
```

---

## 🌟 Entity Intelligence Examples

### **Smart Person Detection**
```markdown
# Madison
**Relationship to NeuraFlash:** Colleague
**Role:** Senior Developer
**Department:** Engineering
**Projects Involved:** PSA Salesforce Implementation
```

### **Contextual Company Notes**
```markdown
# PSA
**Relationship to NeuraFlash:** Client
**Business Needs:** Salesforce automation, payroll integration
**Technologies Used:** Salesforce, AWS Lambda
**Contract Status:** Active Implementation
```

### **Technical Documentation**
```markdown
# AWS Lambda
**Current Status:** Deployed
**Owner/Responsible:** Engineering Team
**Use Cases:** Salesforce automation, data processing
**Business Value:** Reduced manual processing by 80%
```

---

## 🏢 Business Intelligence Features

* **Client Relationship Tracking**: Automatically categorizes contacts and companies
* **Project Documentation**: Links technologies to implementations and outcomes
* **Decision History**: Tracks technical and business decisions with context
* **Knowledge Discovery**: Find patterns across meetings and relationships
* **Expertise Mapping**: Identify who knows what technologies and clients

---

## 🔍 Advanced Configuration

### **Entity Detection Tuning**
```python
# Add custom technology keywords
TECHNOLOGY_KEYWORDS = {
    'Your-Platform', 'Custom-Tool', 'Internal-System'
}

# Exclude false positives
FALSE_POSITIVES = {
    'Common-Word', 'Generic-Term'
}
```

### **Custom Note Templates**
Extend `obsidian/formatter.py` to create custom note structures for your organization.

### **Integration Hooks**
Add custom processing in `entities/manager.py` for CRM integration, Slack notifications, or other business systems.

---

## 📊 Monitoring & Analytics

* **Processing Statistics**: Track entity detection accuracy and processing times
* **Knowledge Growth**: Monitor vault expansion and relationship building
* **Entity Relationships**: Visualize connections between people, companies, and technologies
* **Meeting Insights**: Analyze meeting frequency, participants, and outcomes

---

## 🤝 Contributing

This is a modular, extensible system designed for enhancement:

1. **Fork** the repository
2. **Create** a feature branch
3. **Add** your enhancement to the appropriate module
4. **Test** with your meeting recordings
5. **Submit** a PR with clear documentation

### **Extension Ideas**
- Additional entity types (projects, locations, documents)
- CRM integration (Salesforce, HubSpot)
- Calendar integration for automatic scheduling context
- Slack/Teams notifications for action items
- Custom analysis workflows for specific industries

---

## 📜 License

MIT License - Use, modify, and redistribute freely with attribution.

---

## 🎯 Perfect For

* **Consulting Firms**: Client relationship management and project documentation
* **Software Teams**: Technical decision tracking and knowledge sharing  
* **Sales Organizations**: Client interaction history and opportunity tracking
* **Professional Services**: Meeting documentation and follow-up management
* **Any Business**: Building institutional knowledge from conversations

---

*Transform your meetings into structured knowledge with AI-powered intelligence.*

**Built with ❤️ for knowledge workers who value their conversations.**
