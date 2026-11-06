# kwtSMS for Zabbix

Send Zabbix alerts by SMS through [kwtSMS](https://www.kwtsms.com), the SMS gateway for Kuwait and the Gulf.
One file to import: no package to install on the Zabbix server.

## Features

- Problem, recovery and update alerts by SMS, plus service, discovery, autoregistration and internal events.
- Short SMS-style message templates (what, where, when, event ID), ready to edit.
- English and Arabic alerts. Arabic-Indic and Persian digits in phone numbers and messages are converted.
- Several numbers in one user media, separated by commas. Duplicates and invalid numbers are skipped and reported.
- Long alerts are cut to 7 SMS pages instead of failing.
- Clear errors in the action log, with the fix: wrong API login, zero balance, banned Sender ID, IP not whitelisted.
- Test mode: messages are queued on kwtSMS and never delivered.
- HTTP proxy support.

## Requirements

- Zabbix 7.0 LTS or later (tested on 7.0.32 and 7.4.16).
- The Zabbix server can reach `https://www.kwtsms.com` (directly or through a proxy).
- A kwtSMS account with API access. [Sign up free](https://www.kwtsms.com/signup/).

## Installation

1. Download [`media_kwtsms.yaml`](media_kwtsms.yaml).
2. In Zabbix, go to **Alerts > Media types** and click **Import**. Choose the file and import it.

## Setup in 5 minutes

1. Open the **kwtSMS** media type. Set `username` and `password` to the API username and password of your kwtSMS
   account (not your mobile number).
2. Optional: set `sender` to your own Sender ID (default `KWT-SMS`).
3. Tick **Enabled** and save. The media type ships disabled so it cannot run before it has a login.
4. Click **Test**, enter your number in international format (for example `965` followed by the 8 digit number) and
   send. To try it without delivering anything, set `test_mode` to `1` first, and back to `0` afterwards.
5. For each user who should get SMS alerts: **Users > Users > Media > Add**, type **kwtSMS**, and the phone number
   in **Send to**. Choose the severities this user gets by SMS (for example High and Disaster only).
6. In **Alerts > Actions > Trigger actions**, add **kwtSMS** to the operations of the actions that should send SMS.

### Parameters

| Parameter | Default | What it does |
| --- | --- | --- |
| `username` | placeholder | kwtSMS API username |
| `password` | placeholder | kwtSMS API password |
| `sender` | `KWT-SMS` | Sender ID shown on the phone |
| `test_mode` | `0` | `1` = queued on kwtSMS, not delivered, no credits used |
| `send_to` | `{ALERT.SENDTO}` | Filled by Zabbix from the user media |
| `message` | `{ALERT.MESSAGE}` | Filled by Zabbix from the message template |
| `HTTPProxy` | empty | For example `http://proxy.example.com:3128` |

To keep the password out of the media type screen, create a global macro of type **Secret text** (for example
`{$KWTSMS.PASSWORD}`) under **Administration > Macros** and use the macro as the `password` value.

## Keep alert storms under control

Every SMS uses credits. A flapping trigger on many hosts can send a lot of messages.

- Send only High and Disaster by SMS: set it in each user's media severities, or as an action condition.
- Use escalation steps: e-mail first, SMS only if the problem is still not acknowledged after 10 minutes.
- Keep the message templates short. One SMS page is 160 English characters or 70 Arabic characters.
- Watch your kwtSMS balance. When it reaches zero, the action log shows `ERR010` and alerts stop.

## Arabic

Arabic alerts are sent as Unicode. One SMS page holds 70 Arabic characters (67 in a multi-page message), so keep
Arabic templates short. The message templates can be written in any language.

## Troubleshooting

Failed alerts are listed in **Reports > Action log** with the reason.

| Error | Fix |
| --- | --- |
| `ERR001` | The API is disabled on the account. Enable it in your kwtSMS account settings. |
| `ERR003` | Wrong API username or password. |
| `ERR008` | The Sender ID is banned. Use another one or contact kwtSMS support. |
| `ERR010` | The balance is zero. Recharge your kwtSMS account. |
| `ERR013` | The kwtSMS queue is full. Zabbix tries again (3 attempts, 10 seconds apart). |
| `ERR024` | The Zabbix server IP is not in your kwtSMS API IP whitelist. |
| `ERR026` | Sending to that country is not active on the account. Contact kwtSMS support. |
| `No valid phone number` | Use the full international number, digits only or with `+`. |
| `no JSON answer` | The Zabbix server cannot reach www.kwtsms.com: check the proxy and firewall. |

For more detail, set the media type log level to debug and read the Zabbix server log (lines start with
`[ kwtSMS Webhook ]`).

## Development

The script lives in `src/kwtsms.js`; `media_kwtsms.yaml` is generated from it by `python3 build.py`. Tests run the
script in Duktape, the JavaScript engine inside Zabbix:

```sh
pip install dukpy pyyaml
python3 -m unittest discover -s tests
python3 build.py --check
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## Support

Help: https://www.kwtsms.com/support.html | FAQ: https://www.kwtsms.com/faq/ | support@kwtsms.com

## Security

See [SECURITY.md](SECURITY.md).

## License

MIT, (c) kwtSMS
