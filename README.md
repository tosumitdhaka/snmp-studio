# 🔱 Trishul-SNMP

**Modern SNMP Management Platform**

[![GitHub Stars](https://img.shields.io/github/stars/tosumitdhaka/trishul-snmp?style=for-the-badge)](https://github.com/tosumitdhaka/trishul-snmp/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/tosumitdhaka/trishul-snmp?style=for-the-badge)](https://github.com/tosumitdhaka/trishul-snmp/network)
[![GitHub Issues](https://img.shields.io/github/issues/tosumitdhaka/trishul-snmp?style=for-the-badge)](https://github.com/tosumitdhaka/trishul-snmp/issues)
[![License](https://img.shields.io/github/license/tosumitdhaka/trishul-snmp?style=for-the-badge)](LICENSE)
[![GHCR](https://img.shields.io/badge/GHCR-Packages-blue?style=for-the-badge&logo=github)](https://github.com/tosumitdhaka?tab=packages&repo_name=trishul-snmp)

A web-based SNMP toolkit for network engineers and administrators. Simulate SNMP agents, send/receive traps, walk devices with MIB resolution, browse MIB trees, and manage MIB files—all from a clean, intuitive interface.

**Replace 5+ SNMP tools with one modern platform**

---

## ✨ Features

- 🖥️ **SNMP Simulator** - Run configurable SNMP agent with custom OID values
- 🚶 **Walk & Parse** - Execute SNMP walks with MIB resolution, export to JSON/CSV
- 📡 **Trap Manager** - Send/receive SNMP traps with real-time monitoring
- 📚 **MIB Manager** - Upload, validate MIBs, browse trap library, auto-resolve OIDs with dependency detection
- 🌳 **MIB Browser** - Interactive tree explorer with hierarchical OID navigation, search, and filtering
- 🔐 **Secure** - Session-based authentication with credential management
- 🐳 **Containerized** - One-command Docker deployment with host network support
- 🌐 **Modern UI** - Clean, responsive interface built with Bootstrap 5
- 📊 **Export Data** - JSON/CSV export for walks and trap data
- 🔄 **Real-time** - Live trap receiver with instant OID resolution

---

## 🎯 What Trishul-SNMP Replaces

| Tool | Cost | Trishul-SNMP |
|------|------|--------------|
| **Net-SNMP CLI tools** | Free | ✅ Web UI with no command memorization |
| **snmpsim** | Free | ✅ Test SNMP agent responses with web interface |
| **iReasoning MIB Browser** | $500+ | ✅ Free MIB browser with tree navigation |
| **snmptrapd** | Free | ✅ Real-time trap receiver for testing |
| **Custom scripts** | Time | ✅ Built-in JSON/CSV export functionality |
| **Multiple scattered tools** | Complexity | ✅ One unified platform |

**Save $500+ and consolidate your SNMP workflow.**

---

## 🚀 Quick Start

### One-Command Install

```
curl -fsSL https://raw.githubusercontent.com/tosumitdhaka/trishul-snmp/main/install-trishul-snmp.sh | bash
```

### Access

- **Frontend:** http://localhost:8080
- **Backend API:** http://localhost:8000/docs
- **Default login:** `admin` / `admin123`

⚠️ **Change password immediately in Settings!**

### Custom Ports

```
BACKEND_PORT=9000 FRONTEND_PORT=3000 ./install-trishul-snmp.sh up
```

**[📖 Detailed Installation Guide →](https://github.com/tosumitdhaka/trishul-snmp/wiki/Installation-Guide)**

---

## 🧩 Component Overview

### 🖥️ SNMP Simulator (Server Mode)
Run a configurable SNMP agent on UDP 1061 with custom OID values. Perfect for testing SNMP clients without real hardware.

**Key features:**
- Custom OIDs with any value and type
- SNMPv1/v2c support
- Persistent configuration
- Web-based control

**Use case:** Simulate devices for NMS development and testing.

**[📖 Full Simulator Guide →](https://github.com/tosumitdhaka/trishul-snmp/wiki/SNMP-Simulator-Guide)**

---

### 🚶 Walk & Parse (Client Mode)
Execute SNMP walks against any device with automatic MIB resolution and data export.

**Key features:**
- Automatic OID → name resolution
- Bulk operations (GETBULK)
- JSON/CSV export
- Walk history

**Use case:** Test SNMP agent responses, validate walk implementations.

**[📖 Full Walker Guide →](https://github.com/tosumitdhaka/trishul-snmp/wiki/Walker-Guide)**

---

### 📡 Trap Manager (Client + Server)
Send and receive SNMP traps with real-time monitoring and MIB-based trap browsing.

**Key features:**
- **Trap Sender (Client):** Send v1/v2c traps with custom varbinds
- **Trap Receiver (Server):** Real-time trap display on UDP 1162
- **Trap Library:** Browse 24+ available traps from loaded MIBs
- Auto-populate varbinds from library

**Use case:** Validate trap format/syntax for NMS development.

**[📖 Full Trap Manager Guide →](https://github.com/tosumitdhaka/trishul-snmp/wiki/Trap-Manager-Guide)**

---

### 📚 MIB Manager
Upload, validate, and manage MIB files with automatic dependency resolution.

**Key features:**
- Drag-and-drop upload
- Syntax validation
- Dependency resolution
- Trap enumeration
- Statistics (objects, imports, traps)

**Use case:** Validate MIBs before deployment, centralized MIB library.

**[📖 Full MIB Manager Guide →](https://github.com/tosumitdhaka/trishul-snmp/wiki/MIB-Manager-Guide)**

---

### 🌳 MIB Browser
Interactive tree explorer for navigating OID hierarchies and understanding MIB structures.

**Key features:**
- **Dual views:** By module or standard OID hierarchy
- **Real-time search:** Find OIDs by name, numeric OID, or description
- **Smart filtering:** By module and type (scalars, tables, notifications)
- **Tree navigation:** Expandable with configurable depth (1-5 levels)
- **Details panel:** Full metadata, descriptions, varbinds
- **Integration:** Jump to Walker/Trap Sender with pre-filled data
- **State persistence:** Remembers your position

**Use case:** Explore MIB structures, understand OID relationships, find traps.

**[📖 Full MIB Browser Guide →](https://github.com/tosumitdhaka/trishul-snmp/wiki/MIB-Browser-Guide)**

---

### 🔐 Settings
Manage authentication and system preferences.

**Key features:**
- Change admin password
- Session management
- System information

---

## 🏗️ Architecture

```
┌───────────────────────────────────────────────────┐
│           Web Browser (Port 8080)                 │
│  Dashboard │ Simulator │ Walker │ Traps │ MIBs    │
└─────────────────────┬─────────────────────────────┘
                      │ HTTP/HTTPS
                      │
         ┌────────────▼────────────┐
         │   Nginx (Frontend)      │
         │   Static Files + Proxy  │
         └────────────┬────────────┘
                      │ REST API
                      │
         ┌────────────▼─────────────────────────┐
         │   FastAPI Backend (Port 8000)        │
         │                                      │
         │  ┌────────────────────────────────┐  │
         │  │  MIB Service                   │  │
         │  │  • Parse & validate MIBs       │  │
         │  │  • Build OID trees             │  │
         │  │  • Search & filter             │  │
         │  └────────────────────────────────┘  │
         │                                      │
         │  ┌────────────────────────────────┐  │
         │  │  SNMP Services                 │  │
         │  │  • Simulator (SVR - UDP 1061)  │  │
         │  │  • Trap Sender (CLI)           │  │
         │  │  • Trap Receiver (SVR - 1162)  │  │
         │  │  • Walker (CLI)                │  │
         │  └────────────────────────────────┘  │
         │                                      │
         │  ┌────────────────────────────────┐  │
         │  │  Data Storage (Volume)         │  │
         │  │  /app/data/mibs/               │  │
         │  └────────────────────────────────┘  │
         └──────────────┬───────────────────────┘
                        │ SNMP (UDP)
                        │
         ┌──────────────┴──────────────┐
         │                             │
    ┌────▼─────┐               ┌───────▼────┐
    │  Test    │               │   Test     │
    │ Devices  │               │  Receivers │
    │(Dev/Test)│               │ (Dev/Test) │
    └──────────┘               └────────────┘
```

**Stack:** Python 3.11 • FastAPI • pysnmp • pysmi • Bootstrap 5 • Docker

**[📖 Detailed Architecture →](https://github.com/tosumitdhaka/trishul-snmp/wiki/Architecture-Overview)**

---

## 🎯 Use Cases

### For NMS Development
- ✅ Send test traps to validate receiver format/syntax
- ✅ Receive test traps to validate sender implementation
- ✅ Simulate SNMP agents for client testing
- ✅ Test SNMP walk responses

### For MIB Management
- ✅ Validate MIB syntax and dependencies
- ✅ Explore MIB structures interactively
- ✅ Search OIDs across multiple MIBs
- ✅ Resolve OID names ↔ numeric OIDs

### For Integration Testing
- ✅ Test SNMP integrations without production devices
- ✅ Validate trap handling in dev environments
- ✅ Simulate device responses for QA
- ✅ Export walk data for automated testing

### For Learning & Training
- ✅ Understand SNMP protocol behavior
- ✅ Explore standard MIB structures
- ✅ Practice SNMP operations safely
- ✅ Learn OID hierarchies visually

**[📖 More Use Cases & Examples →](https://github.com/tosumitdhaka/trishul-snmp/wiki)**

---

## 👥 Best For

- 🔧 **Network engineers** testing devices and exploring MIB structures
- 🚀 **DevOps teams** testing SNMP integrations
- 📚 **Students** learning SNMP protocols and MIB hierarchies
- ✅ **QA teams** validating SNMP implementations
- 👥 **Small teams** needing trap monitoring and MIB browsing
- 🧪 **Developers** building SNMP-enabled applications

### ⚠️ Not For

- ❌ Production 24/7 monitoring (use Zabbix, PRTG, LibreNMS)
- ❌ Enterprise-scale NMS (use SolarWinds, Cisco Prime)
- ❌ High-availability monitoring (use dedicated monitoring platforms)

---

## 📚 Documentation

**Complete guides available in [Wiki](https://github.com/tosumitdhaka/trishul-snmp/wiki):**

### Getting Started
- 📖 [Installation Guide](https://github.com/tosumitdhaka/trishul-snmp/wiki/Installation-Guide) - Detailed setup instructions
- 🚀 [First Steps](https://github.com/tosumitdhaka/trishul-snmp/wiki/First-Steps) - 15-minute walkthrough
- ❓ [FAQ](https://github.com/tosumitdhaka/trishul-snmp/wiki/FAQ) - Frequently asked questions
- 📋 [Changelog](https://github.com/tosumitdhaka/trishul-snmp/wiki/Changelog) - Version history 

### User Guides
- 🖥️ [SNMP Simulator Guide](https://github.com/tosumitdhaka/trishul-snmp/wiki/SNMP-Simulator-Guide)
- 🚶 [Walker Guide](https://github.com/tosumitdhaka/trishul-snmp/wiki/Walker-Guide)
- 📡 [Trap Manager Guide](https://github.com/tosumitdhaka/trishul-snmp/wiki/Trap-Manager-Guide)
- 📚 [MIB Manager Guide](https://github.com/tosumitdhaka/trishul-snmp/wiki/MIB-Manager-Guide)
- 🌳 [MIB Browser Guide](https://github.com/tosumitdhaka/trishul-snmp/wiki/MIB-Browser-Guide)

### Technical
- 🏗️ [Architecture Overview](https://github.com/tosumitdhaka/trishul-snmp/wiki/Architecture-Overview)
- 🔧 [API Reference](https://github.com/tosumitdhaka/trishul-snmp/wiki/API-Reference)
- 🛠️ [Development Setup](https://github.com/tosumitdhaka/trishul-snmp/wiki/Development-Setup)
- 🐛 [Troubleshooting](https://github.com/tosumitdhaka/trishul-snmp/wiki/Troubleshooting)

---

## 📰 Featured Article

[![Dev.to Article](https://img.shields.io/badge/Dev.to-Read%20Article-0A0A0A?style=for-the-badge&logo=dev.to)](https://dev.to/tosumitdhaka/building-trishul-snmp-a-modern-web-based-snmp-toolkit-to-replace-500-commercial-tools-3d53)

### 📝 [Building Trishul-SNMP: A Modern Web-Based SNMP Toolkit](https://dev.to/tosumitdhaka/building-trishul-snmp-a-modern-web-based-snmp-toolkit-to-replace-500-commercial-tools-3d53)

**A technical deep dive into building a free, open-source alternative to $500 commercial tools.**

Read about:
- 🏗️ **Architecture decisions** - Why FastAPI, pysnmp, and Docker host network mode
- 🔧 **Technical challenges** - MIB parsing, state persistence, performance optimization
- 💡 **Solutions implemented** - Caching strategies, lazy loading, image optimization
- 📊 **Lessons learned** - 8 months of development insights
- 🎯 **Results** - 150+ stars, 500+ pulls, 3 companies in production

---

## 🤝 Contributing

We welcome contributions! 🎉

[![Contributors](https://img.shields.io/github/contributors/tosumitdhaka/trishul-snmp?style=for-the-badge)](https://github.com/tosumitdhaka/trishul-snmp/graphs/contributors)

**Ways to contribute:**
- 🐛 [Report bugs](https://github.com/tosumitdhaka/trishul-snmp/issues)
- 💡 [Suggest features](https://github.com/tosumitdhaka/trishul-snmp/issues)
- 🔧 [Submit pull requests](https://github.com/tosumitdhaka/trishul-snmp/pulls)
- 📝 [Improve documentation](https://github.com/tosumitdhaka/trishul-snmp/wiki)
- 🌍 Translate the interface
- 🎨 Improve UI/UX
- ⭐ [Star the repo](https://github.com/tosumitdhaka/trishul-snmp)

See [CONTRIBUTING.md](CONTRIBUTING.md) and [Development Setup](https://github.com/tosumitdhaka/trishul-snmp/wiki/Development-Setup) for details.

---

## 💖 Support This Project

Trishul-SNMP is **100% free and open-source** (MIT License).

**If it helps you:**
- ⭐ [Star the repo](https://github.com/tosumitdhaka/trishul-snmp) - Helps others discover it
- 💰 [Sponsor on GitHub](https://github.com/sponsors/tosumitdhaka) - Support development
- ☕ [Buy me a coffee](https://buymeacoffee.com/tosumitdhaka) - One-time donation
- 🐦 [Share on Twitter](https://twitter.com/intent/tweet?text=Check%20out%20Trishul-SNMP) - Spread the word
- 📝 Write a blog post about your experience

[![GitHub Sponsors](https://img.shields.io/github/sponsors/tosumitdhaka?style=for-the-badge&logo=github)](https://github.com/sponsors/tosumitdhaka)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-yellow?style=for-the-badge&logo=buy-me-a-coffee)](https://buymeacoffee.com/tosumitdhaka)

---

## 🚀 Roadmap

### ✅ v1.2.0 (Current)
- [x] MIB Browser with tree navigation
- [x] Search and filter OIDs
- [x] State persistence
- [x] Trap library (24+ traps)

### 🚧 v1.3.0 (In Progress)
- [ ] SNMPv3 authentication (MD5, SHA, AES)
- [ ] Tree export to JSON/CSV
- [ ] Dark mode

### 📋 Planned
- [ ] Scheduled SNMP walks
- [ ] Device/Agent management
- [ ] Multi-language support
      

[Vote on features →](https://github.com/tosumitdhaka/trishul-snmp/issues)

---

## 📊 Project Stats

![GitHub commit activity](https://img.shields.io/github/commit-activity/m/tosumitdhaka/trishul-snmp?style=flat-square)
![GitHub last commit](https://img.shields.io/github/last-commit/tosumitdhaka/trishul-snmp?style=flat-square)
![GitHub code size](https://img.shields.io/github/languages/code-size/tosumitdhaka/trishul-snmp?style=flat-square)

---

### Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

### Recognition

All contributors are recognized in [CONTRIBUTORS.md](CONTRIBUTORS.md) and release notes! 🌟

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

**Free forever. No hidden costs. No feature paywalls.**

---

## 📞 Community & Support

- 💬 [GitHub Discussions](https://github.com/tosumitdhaka/trishul-snmp/discussions) - Ask questions, share ideas
- 🐛 [Issues](https://github.com/tosumitdhaka/trishul-snmp/issues) - Report bugs, request features
- 📧 Email: [sumitdhaka@zohomail.in](mailto:sumitdhaka@zohomail.in)
- 💼 LinkedIn: [Sumit Dhaka](https://www.linkedin.com/in/sumit-dhaka-a5a796b3/)

---

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [pysnmp](https://github.com/etingof/pysnmp) - SNMP library for Python
- [pysmi](https://github.com/etingof/pysmi) - MIB parser and compiler
- [Bootstrap 5](https://getbootstrap.com/) - UI framework
- [Font Awesome](https://fontawesome.com/) - Icons

---

<div align="center">

**Made with 🔱 by [Sumit Dhaka](https://github.com/tosumitdhaka)**

*Trishul-SNMP - Modern SNMP Management Made Simple*

If this project helps you, please consider [⭐ starring it](https://github.com/tosumitdhaka/trishul-snmp) and [💰 sponsoring](https://github.com/sponsors/tosumitdhaka)!

[![GitHub](https://img.shields.io/badge/GitHub-tosumitdhaka-181717?style=for-the-badge&logo=github)](https://github.com/tosumitdhaka)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=for-the-badge&logo=linkedin)](https://www.linkedin.com/in/sumit-dhaka-a5a796b3/)

**[⬆ Back to Top](#-trishul-snmp)**

</div>
