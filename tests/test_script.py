"""Numbers use country code 999 (unassigned, nobody can receive them); the API is mocked.

Runs src/kwtsms.js in Duktape (the JavaScript engine inside Zabbix) with a mocked HttpRequest.

Usage: pip install dukpy pyyaml && python3 -m unittest discover -s tests
"""
import json
import pathlib
import unittest

import dukpy

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = (ROOT / "src" / "kwtsms.js").read_text(encoding="utf-8")

SHIM = """
var Zabbix = {log: function (level, msg) { call_python('log', level, String(msg)); }};
function HttpRequest() { this.headers = []; this.status = 0; }
HttpRequest.prototype.addHeader = function (h) { this.headers.push(h); };
HttpRequest.prototype.setProxy = function (p) { this.proxy = p; };
HttpRequest.prototype.post = function (url, body) {
    var r = call_python('post', url, body, this.headers, this.proxy || '');
    this.status = r[0];
    return r[1];
};
HttpRequest.prototype.getStatus = function () { return this.status; };
"""

BASE = {"username": "zabbix_username", "password": "zabbix_password", "sender": "KWT-SMS",
        "send_to": "99912345678", "message": "PROBLEM High: CPU load\nHost: web01", "test_mode": "1", "HTTPProxy": ""}


class Run:
    def __init__(self, answer=(200, '{"result":"OK","msg-id":"x1","numbers":1,"points-charged":1,"balance-after":9}')):
        self.answer, self.calls, self.logs = answer, [], []

    def __call__(self, **overrides):
        params = dict(BASE, **overrides)
        js = dukpy.JSInterpreter()
        js.export_function("log", lambda level, msg: self.logs.append(msg))

        def post(url, body, headers, proxy):
            self.calls.append({"url": url, "body": json.loads(body), "headers": headers, "proxy": proxy})
            return list(self.answer)

        js.export_function("post", post)
        code = SHIM + "(function (value) {\n" + SCRIPT + "\n})(" + json.dumps(json.dumps(params)) + ");"
        return js.evaljs(code)


class ScriptTest(unittest.TestCase):
    def test_sends_json_with_test_flag_and_user_agent(self):
        run = Run()
        self.assertEqual(run(), "OK (test mode: queued, not delivered)")
        call = run.calls[0]
        self.assertEqual(call["url"], "https://www.kwtsms.com/API/send/")
        self.assertEqual(call["body"]["test"], "1")
        self.assertEqual(call["body"]["sender"], "KWT-SMS")
        self.assertIn("User-Agent: kwtsms-zabbix/1.0.0", call["headers"])
        self.assertIn("Content-Type: application/json", call["headers"])

    def test_live_mode_result(self):
        run = Run()
        self.assertEqual(run(test_mode="0"), "OK")
        self.assertEqual(run.calls[0]["body"]["test"], "0")

    def test_phone_numbers_normalized_deduped_invalid_skipped(self):
        run = Run()
        result = run(send_to="+999 1234 5678, 0099912345678; ٩٩٩١٢٣٤٥٦٧٩,  12, ")
        self.assertEqual(run.calls[0]["body"]["mobile"], "99912345678,99912345679")
        self.assertIn("skipped invalid: 12", result)

    def test_persian_digits(self):
        run = Run()
        run(send_to="۹۹۹۱۲۳۴۵۶۷۰")
        self.assertEqual(run.calls[0]["body"]["mobile"], "99912345670")

    def test_message_cleaned(self):
        run = Run()
        run(message="<b>Disk</b> full \U0001F525 on db​01 ❤️ code ١٢٣ مرحبا")
        self.assertEqual(run.calls[0]["body"]["message"], "Disk full  on db01  code 123 مرحبا")

    def test_newlines_kept_carriage_return_dropped(self):
        run = Run()
        run(message="line1\r\nline2")
        self.assertEqual(run.calls[0]["body"]["message"], "line1\nline2")

    def test_long_english_cut_to_7_pages(self):
        run = Run()
        run(message="a" * 2000)
        msg = run.calls[0]["body"]["message"]
        self.assertEqual(len(msg), 1071)
        self.assertTrue(msg.endswith("..."))

    def test_long_arabic_cut_to_7_pages(self):
        run = Run()
        run(message="ب" * 1000)
        self.assertEqual(len(run.calls[0]["body"]["message"]), 469)

    def test_error_code_mapped_to_hint(self):
        run = Run(answer=(200, '{"result":"ERROR","code":"ERR003","description":"Authentication error"}'))
        with self.assertRaises(dukpy.JSRuntimeError) as cm:
            run()
        self.assertIn("kwtSMS ERR003", str(cm.exception))
        self.assertIn("not your mobile number", str(cm.exception))

    def test_non_json_answer(self):
        run = Run(answer=(502, "<html>Bad gateway</html>"))
        with self.assertRaises(dukpy.JSRuntimeError) as cm:
            run()
        self.assertIn("HTTP 502", str(cm.exception))

    def test_placeholder_credentials_refused_before_any_request(self):
        run = Run()
        with self.assertRaises(dukpy.JSRuntimeError) as cm:
            run(username="<PLACE API USERNAME>")
        self.assertIn('"username"', str(cm.exception))
        self.assertEqual(run.calls, [])

    def test_unresolved_send_to_and_no_valid_number(self):
        run = Run()
        with self.assertRaises(dukpy.JSRuntimeError):
            run(send_to="{ALERT.SENDTO}")
        with self.assertRaises(dukpy.JSRuntimeError) as cm:
            run(send_to="abc, 123")
        self.assertIn("No valid phone number", str(cm.exception))
        self.assertEqual(run.calls, [])

    def test_proxy_passed(self):
        run = Run()
        run(HTTPProxy="http://proxy.local:3128")
        self.assertEqual(run.calls[0]["proxy"], "http://proxy.local:3128")

    def test_empty_after_cleaning(self):
        run = Run()
        with self.assertRaises(dukpy.JSRuntimeError) as cm:
            run(message="\U0001F525\U0001F525")
        self.assertIn("empty after cleaning", str(cm.exception))


class YamlTest(unittest.TestCase):
    def test_yaml_matches_script_and_ships_disabled(self):
        import yaml
        media = yaml.safe_load((ROOT / "media_kwtsms.yaml").read_text(encoding="utf-8"))["zabbix_export"]["media_types"][0]
        self.assertEqual(media["script"].rstrip("\n"), SCRIPT.rstrip("\n"))
        self.assertEqual(media["status"], "DISABLED")
        params = {p["name"]: p["value"] for p in media["parameters"]}
        self.assertEqual(params["test_mode"], "0")
        self.assertTrue(params["password"].startswith("<"))


if __name__ == "__main__":
    unittest.main()
