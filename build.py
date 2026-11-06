#!/usr/bin/env python3
"""Build media_kwtsms.yaml (the file customers import into Zabbix) from src/kwtsms.js.

Usage: python3 build.py          write media_kwtsms.yaml
       python3 build.py --check  exit 1 if media_kwtsms.yaml is not up to date (CI)
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent

PARAMETERS = [
    ("HTTPProxy", ""),
    ("message", "{ALERT.MESSAGE}"),
    ("password", "<PLACE API PASSWORD>"),
    ("send_to", "{ALERT.SENDTO}"),
    ("sender", "KWT-SMS"),
    ("test_mode", "0"),
    ("username", "<PLACE API USERNAME>"),
]

# Short SMS-style templates: what, where, when, event id. One SMS page where the names allow.
TEMPLATES = [
    ("TRIGGERS", "PROBLEM", "PROBLEM {EVENT.SEVERITY}: {EVENT.NAME}\nHost: {HOST.NAME}\n{EVENT.DATE} {EVENT.TIME} | ID {EVENT.ID}"),
    ("TRIGGERS", "RECOVERY", "RESOLVED: {EVENT.NAME}\nHost: {HOST.NAME}\nAfter {EVENT.DURATION} | ID {EVENT.ID}"),
    ("TRIGGERS", "UPDATE", "UPDATE: {EVENT.NAME}\n{USER.FULLNAME} {EVENT.UPDATE.ACTION}\n{EVENT.UPDATE.MESSAGE}"),
    ("DISCOVERY", "PROBLEM", "DISCOVERY: {DISCOVERY.DEVICE.STATUS} {DISCOVERY.DEVICE.IPADDRESS}\nRule: {DISCOVERY.RULE.NAME}"),
    ("AUTOREGISTRATION", "PROBLEM", "AUTOREGISTRATION: {HOST.HOST} {HOST.IP}"),
    ("INTERNAL", "PROBLEM", "INTERNAL: {EVENT.NAME}\nHost: {HOST.NAME} | ID {EVENT.ID}"),
    ("INTERNAL", "RECOVERY", "INTERNAL RESOLVED: {EVENT.NAME}\nHost: {HOST.NAME} | ID {EVENT.ID}"),
    ("SERVICE", "PROBLEM", "SERVICE {EVENT.SEVERITY}: {SERVICE.NAME}\n{EVENT.NAME} | ID {EVENT.ID}"),
    ("SERVICE", "RECOVERY", "SERVICE RESOLVED: {SERVICE.NAME}\nAfter {EVENT.DURATION} | ID {EVENT.ID}"),
    ("SERVICE", "UPDATE", "SERVICE {EVENT.UPDATE.SEVERITY}: {SERVICE.NAME}\nAge {EVENT.AGE}"),
]

DESCRIPTION = (
    "Send Zabbix alerts by SMS through kwtSMS (kwtsms.com).\n"
    "\n"
    "1. Set username and password to the API username and password of your kwtSMS account.\n"
    "2. Optional: sender (default KWT-SMS), test_mode (1 = queued, not delivered; no credits used).\n"
    "3. Enable this media type, then give each user a kwtSMS media with the phone number in international format.\n"
    "\n"
    "https://github.com/kwtsms/kwtsms-zabbix"
)


def q(s):
    return "'" + s.replace("'", "''") + "'"


def block(text, indent):
    pad = " " * indent
    return "\n".join((pad + line) if line else "" for line in text.split("\n"))


def build():
    script = (ROOT / "src" / "kwtsms.js").read_text(encoding="utf-8").rstrip("\n")
    out = ["zabbix_export:", "  version: '7.0'", "  media_types:", "    - name: kwtSMS", "      type: WEBHOOK",
           "      parameters:"]
    for name, value in PARAMETERS:
        out += ["        - name: " + name, "          value: " + q(value)]
    out += ["      status: DISABLED", "      attempts: '3'", "      attempt_interval: 10s",
            "      script: |", block(script, 8), "      timeout: 30s",
            "      description: |", block(DESCRIPTION, 8), "      message_templates:"]
    for source, mode, message in TEMPLATES:
        out += ["        - event_source: " + source, "          operation_mode: " + mode,
                "          subject: " + q(message.split("\n")[0]), "          message: |", block(message, 12)]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    target = ROOT / "media_kwtsms.yaml"
    text = build()
    if "--check" in sys.argv:
        ok = target.exists() and target.read_text(encoding="utf-8") == text
        print("media_kwtsms.yaml up to date" if ok else "media_kwtsms.yaml is stale: run python3 build.py")
        sys.exit(0 if ok else 1)
    target.write_text(text, encoding="utf-8")
    print("wrote", target.name, len(text), "bytes")
