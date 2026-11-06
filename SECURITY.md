# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |

## Reporting a vulnerability

Please do not report security vulnerabilities through public GitHub issues.

Email **security@kwtsms.com** with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact

You will receive a response within 48 hours. If the issue is confirmed, a patch will be released as soon as possible.

## Scope

The media type runs inside the Zabbix server and makes one HTTPS request to the kwtSMS API per alert. Key security
properties:
- The API password is never written to the Zabbix log, at any log level.
- Requests go only to `https://www.kwtsms.com/API/send/`, with certificate verification by the Zabbix server.
- No dependencies, no dynamic code execution.
- The media type ships disabled with placeholder credentials. Store the password in a Secret text global macro to hide
  it from the media type screen and from exports.
