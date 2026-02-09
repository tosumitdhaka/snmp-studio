# Changelog

All notable changes to Trishul-SNMP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] - 2026-02-09

### Added
- **MIB Browser** - Interactive tree explorer with dual view modes (by module/OID hierarchy)
- **Tree Navigation** - Expandable OID hierarchy with configurable depth (1-5 levels, default: 3)
- **Real-time Search** - Find OIDs by name, numeric OID, or description with 500ms debounce
- **Smart Filtering** - Filter by module and object type (scalars, tables, columns, notifications)
- **Details Panel** - Compact metadata display with breadcrumb navigation
- **Seamless Integration** - Jump to Walker/Trap Sender with pre-filled data
- **State Persistence** - Remembers filters, search, expanded nodes, and selected OID across page switches
- **System MIB Detection** - Visual distinction between loaded MIBs (blue) and built-in MIBs (gray)
- **Trap Library Enhancement** - Shows all 24 traps (19 from loaded MIBs + 5 from system MIBs)
- **Dashboard Card** - Added MIB Browser card with purple theme
- **Depth Control** - Dropdown selector for expansion depth with expand/collapse buttons
- **Copy Buttons** - One-click copy for OID and full name in details panel
- **Loading Indicators** - Spinner and notifications for expand/collapse operations

### Fixed
- **Trap Count Consistency** - Dashboard, MIB Manager, and Browser now show consistent trap counts
- **MIB Delete Function** - Fixed error handling when deleting MIB files
- **State Restoration** - Fixed search clear icon visibility after page switch
- **Expanded State** - Tree expansion state now properly restored after navigation
- **Selected Node** - Details panel correctly loads after page switch
- **System MIB Badge** - SNMPv2-MIB and RMON-MIB correctly marked as system only when not loaded

### Changed
- **UI/UX Consistency** - Unified styling across all components
- **Trap Manager** - Renamed "Available Traps" to "Trap Library" for clarity
- **Dashboard Polling** - Reduced from 5s to 10s for better performance
- **Backend Caching** - Added 60-second cache for trap list API calls
- **Component Overview** - Updated README with compact overview of all 6 components

### Performance
- **Backend Caching** - Trap list cached for 60 seconds (reduces repeated queries)
- **Lazy Loading** - Tree nodes load children on-demand
- **Efficient Rendering** - Only visible nodes rendered in tree
- **Debounced Search** - 500ms delay prevents excessive API calls

---

## [1.1.7] - 2026-01-15

### Changed
- Rebranded to Trishul-SNMP
- Improved documentation and contributing guidelines

---

## [1.1.6] - 2025-12-20

### Added
- Docker volume support for data persistence
- Backup/restore functionality
- Smart GHCR authentication (public/private images)

---

## [1.1.5] - 2025-11-10

### Added
- One-command installer script
- Customizable backend and frontend ports
- Host network mode for dynamic SNMP ports

### Changed
- Improved UI
- Updated app icon

---

## [1.1.4] - 2025-10-05

### Changed
- Updated UI visuals and fixes

---

## [1.1.3] - 2025-09-15

### Added
- Enhanced trap management with real-time display
- JSON/CSV export for walk results

### Changed
- Improved error handling and logging

---

## [1.1.2] - 2025-08-20

### Added
- MIB browser with trap enumeration

### Fixed
- Trap sender fixes
- SNMP walker fixes

---

## [1.1.1] - 2025-07-10

### Fixed
- SNMP walk simulator fixes

---

## [1.0.0] - 2025-06-01

### Added
- Initial release
- SNMP simulator with custom OIDs
- Walk & parse functionality
- Trap sender and receiver
- MIB manager with validation
- Session-based authentication
- Docker deployment
- Bootstrap 5 UI

---

## Legend

- **Added** - New features
- **Changed** - Changes in existing functionality
- **Deprecated** - Soon-to-be removed features
- **Removed** - Removed features
- **Fixed** - Bug fixes
- **Security** - Vulnerability fixes
- **Performance** - Performance improvements

---

[1.2.0]: https://github.com/tosumitdhaka/trishul-snmp/compare/v1.1.7...v1.2.0
[1.1.7]: https://github.com/tosumitdhaka/trishul-snmp/compare/v1.1.6...v1.1.7
[1.1.6]: https://github.com/tosumitdhaka/trishul-snmp/compare/v1.1.5...v1.1.6
[1.1.5]: https://github.com/tosumitdhaka/trishul-snmp/compare/v1.1.4...v1.1.5
[1.1.4]: https://github.com/tosumitdhaka/trishul-snmp/compare/v1.1.3...v1.1.4
[1.1.3]: https://github.com/tosumitdhaka/trishul-snmp/compare/v1.1.2...v1.1.3
[1.1.2]: https://github.com/tosumitdhaka/trishul-snmp/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/tosumitdhaka/trishul-snmp/compare/v1.0.0...v1.1.1
[1.0.0]: https://github.com/tosumitdhaka/trishul-snmp/releases/tag/v1.0.0
