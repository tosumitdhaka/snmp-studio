# 🔱 Trishul-SNMP

**Modern SNMP Management Platform**

[![GitHub Stars](https://img.shields.io/github/stars/tosumitdhaka/trishul-snmp?style=for-the-badge)](https://github.com/tosumitdhaka/trishul-snmp/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/tosumitdhaka/trishul-snmp?style=for-the-badge)](https://github.com/tosumitdhaka/trishul-snmp/network)
[![GitHub Issues](https://img.shields.io/github/issues/tosumitdhaka/trishul-snmp?style=for-the-badge)](https://github.com/tosumitdhaka/trishul-snmp/issues)
[![License](https://img.shields.io/github/license/tosumitdhaka/trishul-snmp?style=for-the-badge)](LICENSE)
[![Docker Pulls](https://img.shields.io/docker/pulls/tosumitdhaka/trishul-snmp-backend?style=for-the-badge)](https://github.com/tosumitdhaka/trishul-snmp/pkgs/container/trishul-snmp-backend)

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

✅ **Net-SNMP CLI tools** → Web UI with no command memorization  
✅ **snmpsim** → Custom OID simulator with web interface  
✅ **iReasoning MIB Browser ($500)** → Free MIB browser with tree navigation  
✅ **snmptrapd** → Real-time trap receiver with web display  
✅ **Custom scripts** → Built-in JSON/CSV export functionality  
✅ **Multiple scattered tools** → One unified platform

---

## 🚀 Quick Start

### One-Command Install

```
curl -fsSL https://raw.githubusercontent.com/tosumitdhaka/trishul-snmp/main/install-trishul-snmp.sh | bash
```

### Manual Install

```
# Download installer
curl -fsSL https://raw.githubusercontent.com/tosumitdhaka/trishul-snmp/main/install-trishul-snmp.sh -o install-trishul-snmp.sh
chmod +x install-trishul-snmp.sh

# Deploy (default ports: 8000, 8080)
./install-trishul-snmp.sh up

# Custom ports
BACKEND_PORT=9000 FRONTEND_PORT=3000 ./install-trishul-snmp.sh up
```

### Access

- **Frontend:** http://localhost:8080
- **Backend API:** http://localhost:8000
- **Default login:** `admin` / `admin123`

---

## 📖 Commands

```
./install-trishul-snmp.sh up              # Start containers
./install-trishul-snmp.sh down            # Stop containers
./install-trishul-snmp.sh restart         # Restart containers
./install-trishul-snmp.sh logs            # View backend logs
./install-trishul-snmp.sh status          # Check status
./install-trishul-snmp.sh backup          # Backup data to tar.gz
./install-trishul-snmp.sh restore <file>  # Restore from backup
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Web Browser (Port 8080)         │
└────────────────┬────────────────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
┌───▼────┐              ┌─────▼──────┐
│ Nginx  │◄────────────►│  FastAPI   │
│ :8080  │     API      │   :8000    │
└────────┘              └─────┬──────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
              ┌─────▼─────┐      ┌──────▼──────┐
              │ Simulator │      │  Receiver   │
              │ UDP: 1061 │      │ UDP: 1162   │
              └───────────┘      └─────────────┘
```

**Stack:** Python 3.11 • FastAPI • pysnmp • pysmi • Nginx • Docker

---

## 🧩 Component Overview

### 🖥️ **SNMP Simulator**
Run a configurable SNMP agent on UDP port 1061 with custom OID values. Perfect for testing SNMP clients without real hardware.
- **Custom OIDs** - Define any OID with custom values and types
- **SNMPv1/v2c** - Support for community-based authentication
- **Persistent data** - OID values survive restarts
- **Web control** - Start/stop agent from dashboard

### 🚶 **Walk & Parse**
Execute SNMP walks against any device with automatic MIB resolution and data export.
- **MIB resolution** - Converts numeric OIDs to human-readable names
- **Bulk operations** - Walk entire MIB trees efficiently
- **Export formats** - JSON and CSV export for analysis
- **History** - View previous walk results

### 📡 **Trap Manager**
Send and receive SNMP traps with real-time monitoring and MIB-based trap browsing.
- **Trap sender** - Send v1/v2c traps with custom varbinds
- **Trap receiver** - Real-time trap display on UDP port 1162
- **Trap library** - Browse 24+ available traps from loaded MIBs
- **Auto-populate** - Select trap from library to auto-fill varbinds

### 🌳 **MIB Browser**
Interactive tree explorer for navigating OID hierarchies and understanding MIB structures.
- **Dual views** - Browse by module or standard OID hierarchy
- **Real-time search** - Find OIDs by name, numeric OID, or description
- **Smart filtering** - Filter by module and type (scalars, tables, notifications)
- **Tree navigation** - Expandable hierarchy with configurable depth (1-5 levels)
- **Details panel** - View full metadata, descriptions, and varbinds
- **Integration** - Jump to Walker or Trap Sender with pre-filled data
- **State persistence** - Remembers your position across page switches

### 📚 **MIB Manager**
Upload, validate, and manage MIB files with automatic dependency resolution.
- **Upload MIBs** - Drag-and-drop or file selection
- **Validation** - Automatic syntax checking and dependency detection
- **Trap enumeration** - Lists all notification types per MIB
- **Statistics** - View object counts, imports, and trap counts
- **Delete/Reload** - Manage MIB lifecycle with hot-reload

### 🔐 **Settings**
Manage authentication and system preferences.
- **Credentials** - Change admin password
- **Session management** - Secure token-based authentication
- **System info** - View version and configuration

---

## 🔧 Configuration

### Environment Variables

```
BACKEND_PORT=8000    # Backend API port (default: 8000)
FRONTEND_PORT=8080   # Frontend web port (default: 8080)
GHCR_TOKEN=xxx       # GitHub PAT (optional for public images)
```

### Examples

```
# Default ports
./install-trishul-snmp.sh up

# Custom ports
BACKEND_PORT=9000 FRONTEND_PORT=3000 ./install-trishul-snmp.sh up

# With authentication token
GHCR_TOKEN=ghp_xxx ./install-trishul-snmp.sh up
```

---

## 📦 Docker Images

- **Backend:** `ghcr.io/tosumitdhaka/trishul-snmp-backend:latest`
- **Frontend:** `ghcr.io/tosumitdhaka/trishul-snmp-frontend:latest`

---

## 🛠️ Development

### Local Development

```
# Clone repository
git clone https://github.com/tosumitdhaka/trishul-snmp.git
cd trishul-snmp

# Start with docker-compose
docker-compose up -d

# Access
open http://localhost:8080
```

### Build Images

```
# Build backend
docker build -t trishul-snmp-backend ./backend

# Build frontend
docker build -t trishul-snmp-frontend ./frontend

# Build both with docker-compose
docker-compose build
```

---

## 👥 Best For

- 🔧 **Network engineers** testing devices and exploring MIB structures
- 🚀 **DevOps teams** testing SNMP integrations
- 📚 **Students** learning SNMP protocols and MIB hierarchies
- ✅ **QA teams** validating SNMP implementations
- 👥 **Small teams** needing trap monitoring and MIB browsing
- 🧪 **Developers** building SNMP-enabled applications

---

## ⚠️ Not For

- ❌ Production 24/7 monitoring (use Zabbix, PRTG, LibreNMS)
- ❌ Enterprise-scale NMS (use SolarWinds, Cisco Prime)
- ❌ High-availability monitoring (use dedicated monitoring platforms)

---

## 💖 Support This Project

Trishul-SNMP is **100% free and open-source**. If it helps you, consider:

- ⭐ **Star this repo** - Helps others discover it
- 💰 **[Sponsor on GitHub](https://github.com/sponsors/tosumitdhaka)** - Support development
- ☕ **[Buy me a coffee](https://buymeacoffee.com/tosumitdhaka)** - One-time donation
- 🐦 **[Share on Twitter](https://twitter.com/intent/tweet?text=Check%20out%20Trishul-SNMP%20-%20Modern%20SNMP%20Management%20Platform%20%F0%9F%94%B1%20https%3A%2F%2Fgithub.com%2Ftosumitdhaka%2Ftrishul-snmp)** - Spread the word
- 📝 **Write a blog post** - Share your experience
- 🤝 **Contribute code** - See [CONTRIBUTING.md](CONTRIBUTING.md)

[![GitHub Sponsors](https://img.shields.io/github/sponsors/tosumitdhaka?style=for-the-badge&logo=github)](https://github.com/sponsors/tosumitdhaka)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-yellow?style=for-the-badge&logo=buy-me-a-coffee)](https://buymeacoffee.com/tosumitdhaka)

---

## 🤝 Contributing

We welcome contributions from the community! 🎉

[![Contributors](https://img.shields.io/github/contributors/tosumitdhaka/trishul-snmp?style=for-the-badge)](https://github.com/tosumitdhaka/trishul-snmp/graphs/contributors)

### Ways to Contribute

- 🐛 **Report bugs** - Open an issue
- 💡 **Suggest features** - Share your ideas
- 📝 **Improve documentation** - Fix typos, add examples
- 🔧 **Submit pull requests** - Add features, fix bugs
- 🌍 **Translate** - Help localize the interface
- 🎨 **Design** - Improve UI/UX
- 📹 **Create content** - Tutorials, videos, blog posts

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Recognition

All contributors are recognized in [CONTRIBUTORS.md](CONTRIBUTORS.md) and release notes! 🌟

---

## 💼 Need Professional Help?

I offer consulting services for:

- 🔧 **SNMP implementation & troubleshooting**
- 🔗 **Custom integrations** with monitoring systems
- 📊 **MIB development** and customization
- 🏗️ **Architecture consulting** for network monitoring

📧 **Contact:** [sumitdhaka@zohomail.in](mailto:sumitdhaka@zohomail.in)  
💼 **LinkedIn:** [Sumit Dhaka](https://www.linkedin.com/in/sumit-dhaka-a5a796b3/)

---

## 🌟 Sponsors

### Gold Sponsors 💎

*[Become a Gold Sponsor](https://github.com/sponsors/tosumitdhaka) - $500/month*

### Silver Sponsors 🚀

*[Become a Silver Sponsor](https://github.com/sponsors/tosumitdhaka) - $100/month*

### Bronze Sponsors 🌟

*[Become a Bronze Sponsor](https://github.com/sponsors/tosumitdhaka) - $25/month*

### Community Supporters ☕

Thank you to all our supporters! Your contributions help maintain and improve Trishul-SNMP. 🙏

---

## 📝 Changelog

### v1.2.0 (Current) - MIB Browser Release 🌳
- ✨ **NEW: MIB Browser** - Interactive tree explorer with dual view modes
- ✨ **Tree Navigation** - Expandable OID hierarchy with configurable depth (1-5 levels)
- ✨ **Smart Search** - Real-time search by name, OID, or description
- ✨ **Advanced Filtering** - Filter by module and object type (scalars, tables, notifications)
- ✨ **Detailed Panel** - Compact metadata display with breadcrumb navigation
- ✨ **Seamless Integration** - Jump to Walker/Trap Sender with pre-filled data
- ✨ **Trap Library** - Enhanced trap manager
- 🐛 **Fixed** - MIB delete function error handling
- 🐛 **Fixed** - Trap count consistency across dashboard, manager, and browser
- 🎨 **Dashboard** - Added MIB Browser card

### v1.1.7
- ✅ Rebranded to Trishul-SNMP
- ✅ Improved documentation and contributing guidelines

### v1.1.6
- ✅ Docker volume support for data persistence
- ✅ Backup/restore functionality
- ✅ Smart GHCR authentication (public/private images)

### v1.1.5
- ✅ One-command installer script
- ✅ Customizable backend and frontend ports
- ✅ Host network mode for dynamic SNMP ports
- ✅ Improved UI
- ✅ App icon updated

### v1.1.4
- ✅ Updated UI visuals and fixes

### v1.1.3
- ✅ Enhanced trap management with real-time display
- ✅ JSON/CSV export for walk results
- ✅ Improved error handling and logging

### v1.1.2
- ✅ MIB browser with trap enumeration
- ✅ Trap sender fixes
- ✅ SNMP walker fixes

### v1.1.1
- ✅ SNMP walk simulator fixes

### v1.0.0
- 🎉 Initial release
- ✅ SNMP simulator with custom OIDs
- ✅ Walk & parse functionality
- ✅ Trap sender and receiver
- ✅ MIB manager with validation

---

## 🏷️ Keywords

`snmp` `snmp-simulator` `snmp-trap` `mib-browser` `mib-tree` `oid-explorer` `network-management` `network-monitoring` `snmpwalk` `snmptrap` `docker` `fastapi` `python` `devops` `sysadmin` `netops` `open-source` `self-hosted` `monitoring` `observability` `infrastructure` `network-tools`

---

## 🔗 Related Projects

- [Net-SNMP](http://www.net-snmp.org/) - Industry-standard SNMP CLI tools
- [snmpsim](https://github.com/etingof/snmpsim) - SNMP agent simulator
- [Zabbix](https://www.zabbix.com/) - Enterprise monitoring solution
- [LibreNMS](https://www.librenms.org/) - Open-source network monitoring
- [Prometheus](https://prometheus.io/) - Monitoring and alerting toolkit

---

## 📊 Comparison

| Feature | Net-SNMP | iReasoning | Trishul-SNMP |
|---------|----------|------------|--------------|
| **SNMP Simulator** | ✅ CLI | ❌ | ✅ Web UI |
| **Walk Devices** | ✅ CLI | ✅ GUI | ✅ Web + Export |
| **Send Traps** | ✅ CLI | ✅ GUI | ✅ Web + MIB Browse |
| **Receive Traps** | ✅ CLI | ❌ | ✅ Web + Real-time |
| **MIB Manager** | ✅ CLI | ✅ GUI | ✅ Web + Validate |
| **MIB Browser** | ❌ | ✅ GUI | ✅ Web + Tree Nav |
| **OID Search** | ❌ | ✅ | ✅ Real-time |
| **Export JSON/CSV** | ❌ | ✅ | ✅ |
| **Web-Based** | ❌ | ❌ | ✅ |
| **Docker Deploy** | ❌ | ❌ | ✅ |
| **Free** | ✅ | ❌ ($500+) | ✅ |
| **Open Source** | ✅ | ❌ | ✅ |

---

## 🎓 Learning Resources

- 📖 [SNMP Basics Tutorial](https://github.com/tosumitdhaka/trishul-snmp/wiki/SNMP-Basics) *(coming soon)*
- 📖 [MIB Browser Guide](https://github.com/tosumitdhaka/trishul-snmp/wiki/MIB-Browser-Guide) *(coming soon)*
- 🎥 [Video Tutorials](https://www.youtube.com/@tosumitdhaka) *(coming soon)*
- 📝 [Blog Posts](https://dev.to/tosumitdhaka) *(coming soon)*
- 💬 [Community Discord](https://discord.gg/tosumitdhaka) *(coming soon)*

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

**Free forever. No hidden costs. No feature paywalls.**

---

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- SNMP implementation by [pysnmp](https://github.com/etingof/pysnmp)
- MIB parsing by [pysmi](https://github.com/etingof/pysmi)
- UI powered by [Bootstrap 5](https://getbootstrap.com/)
- Icons by [Font Awesome](https://fontawesome.com/) & [Bootstrap Icons](https://icons.getbootstrap.com/)

---

## 📞 Community & Support

- 💬 **GitHub Discussions:** [Ask questions, share ideas](https://github.com/tosumitdhaka/trishul-snmp/discussions)
- 🐛 **Issues:** [Report bugs, request features](https://github.com/tosumitdhaka/trishul-snmp/issues)
- 📧 **Email:** [sumitdhaka@zohomail.in](mailto:sumitdhaka@zohomail.in)
- 💼 **LinkedIn:** [Sumit Dhaka](https://www.linkedin.com/in/sumit-dhaka-a5a796b3/)

---

## 🚀 Deployment Options

### Recommended Hosting

- **[Railway.app](https://railway.app)** - Easy deployment with $5/month free credit
- **[Render.com](https://render.com)** - Free tier with 750 hours/month
- **[Fly.io](https://fly.io)** - Global edge deployment
- **[Oracle Cloud](https://cloud.oracle.com)** - Always free tier (2 VMs, 200GB)
- **[DigitalOcean](https://m.do.co/c/cc2178d50ce7)** - $200 credit for new users

### Self-Hosted

Deploy on your own infrastructure using the one-command installer or Docker Compose.

---

## 📈 Project Stats

![GitHub commit activity](https://img.shields.io/github/commit-activity/m/tosumitdhaka/trishul-snmp?style=flat-square)
![GitHub last commit](https://img.shields.io/github/last-commit/tosumitdhaka/trishul-snmp?style=flat-square)
![GitHub code size](https://img.shields.io/github/languages/code-size/tosumitdhaka/trishul-snmp?style=flat-square)

---

## 🎯 Roadmap

### ✅ Completed (v1.2.0)
- [x] Full MIB tree browser with dual view modes
- [x] Interactive OID navigation with expandable tree
- [x] Search OIDs across MIBs with real-time results
- [x] View OID descriptions, syntax, and metadata
- [x] Filter by module and object type
- [x] Seamless integration with Walker and Trap Sender
- [x] State persistence across page switches
- [x] Configurable expansion depth (1-5 levels)

### 🚧 In Progress
- [ ] SNMPv3 authentication support (MD5, SHA, AES)
- [ ] Scheduled SNMP walks with cron-like syntax
- [ ] Email/Slack/Webhook notifications for traps

### 📋 Planned
- [ ] API rate limiting and authentication keys
- [ ] Bulk device management (import/export CSV)
- [ ] Enhanced file exports
- [ ] Advanced trap filtering with regex support
- [ ] Mobile-responsive improvements for tablets
- [ ] Dark mode theme
- [ ] Multi-language support (i18n)
- [ ] SNMP SET operations in Walker
- [ ] MIB compiler for custom MIBs
- [ ] Export MIB tree to PDF/PNG

See [Issues](https://github.com/tosumitdhaka/trishul-snmp/issues) for detailed roadmap and vote on features!

---


<div align="center">

**Made with 🔱 by [Sumit Dhaka](https://github.com/tosumitdhaka)**

*Trishul-SNMP - Modern SNMP Management Made Simple*

If this project helps you, please consider [⭐ starring it](https://github.com/tosumitdhaka/trishul-snmp) and [💰 sponsoring](https://github.com/sponsors/tosumitdhaka)!

---

[![GitHub](https://img.shields.io/badge/GitHub-tosumitdhaka-181717?style=for-the-badge&logo=github)](https://github.com/tosumitdhaka)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=for-the-badge&logo=linkedin)](https://www.linkedin.com/in/sumit-dhaka-a5a796b3/)

**[⬆ Back to Top](#-trishul-snmp)**

</div>
