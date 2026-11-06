# Changelog

All notable changes to this project are documented in this file.

## [1.0.0] - 2026-11-06

### Added

- kwtSMS webhook media type for Zabbix 7.0 and later: SMS alerts for problems, recoveries, updates, services, discovery, autoregistration and internal events.
- Phone numbers normalized (international format, Arabic-Indic and Persian digits), duplicates and invalid numbers skipped.
- Messages cleaned (HTML, emoji and hidden characters removed) and cut to 7 SMS pages.
- Error messages with the fix for each kwtSMS error code.
- Test mode, HTTP proxy, User-Agent kwtsms-zabbix/1.0.0.
