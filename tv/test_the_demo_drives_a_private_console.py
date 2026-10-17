# -*- coding: utf-8 -*-
"""REG-2275 (#18 / #73) — THE PRE-PUSH DEMO DRIVES A PRIVATE CONSOLE.

demo_console.mjs opened http://127.0.0.1:${TV_CONTROL_PORT || 17772}/, and journey j3 clicks the
on button whenever that page is on, sim, or stopping. The pre-push hook, when :17772 was silent,
started control_app with --no-open, which binds his port, then ran the demo against it.

His 2026-10-13 authorization is a private console. This law never boots one and never binds a
port. It reads the demo and the hook. The demo must refuse his two ports, hand its child both a
control port and an agent port of its own (the spread of the parent environment comes first, then
the overwrite, so an inherited 17772 does not win), and page.goto that base. The hook must not
start a console and must still run the demos at both call sites.
"""
import io
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEMO = os.path.join(HERE, "demo_console.mjs")
HOOK = os.path.join(ROOT, "hooks", "pre-push")

HIS_LINE = "const HIS_PORTS = new Set([17771, 17772]);"
ENV_BLOCK = (
    "    ...process.env,\n"
    "    TV_CONTROL_PORT: String(port),\n"
    "    TV_PORT: String(agent),\n"
)
SPAWN_LINE = "spawn(py, [path.join(DEMO_DIR, 'control_app.py'), '--no-open'],"


def _js(path):
    with io.open(path, encoding="utf-8") as fh:
        raw = fh.read()
    raw = re.sub(r"/\*.{0,4000}?\*/", "", raw, flags=re.S)
    return "\n".join(line for line in raw.split("\n") if not line.strip().startswith("//"))


def _sh(path):
    with io.open(path, encoding="utf-8") as fh:
        raw = fh.read()
    return "\n".join(re.sub(r"#.*$", "", line) for line in raw.split("\n"))


class TheDemoDrivesAPrivateConsole(unittest.TestCase):

    def test_the_fallback_to_his_port_is_gone(self):
        code = _js(DEMO)
        self.assertEqual(code.count("TV_CONTROL_PORT || 17772"), 0,
                         "the demo still falls open on his console port")
        self.assertEqual(code.count(HIS_LINE), 1,
                         "his two ports are not the one refused set")

    def test_the_child_env_overwrites_inherited_ports(self):
        code = _js(DEMO)
        self.assertEqual(code.count(ENV_BLOCK), 1,
                         "the private app does not overwrite an inherited control port and agent port")
        self.assertEqual(code.count(SPAWN_LINE), 1,
                         "the demo does not boot control_app with --no-open")
        self.assertLess(code.find(ENV_BLOCK), code.find(SPAWN_LINE),
                        "the port overwrite is not the env the child is given")

    def test_goto_uses_the_booted_base(self):
        code = _js(DEMO)
        assign = code.find("URL = target.base;")
        goto = code.find("page.goto(URL,")
        self.assertEqual(code.count("URL = target.base;"), 1)
        self.assertEqual(code.count("page.goto(URL,"), 1)
        self.assertGreaterEqual(assign, 0, "the runner no longer takes the target the boot returned")
        self.assertLess(assign, goto, "page.goto runs before the private base is chosen")
        self.assertEqual(code.count("return { base: await bootPrivate(), owned: true };"), 1,
                         "a refused or missing TV_DEMO_PORT does not boot a private console")
        self.assertIn("!HIS_PORTS.has(n)", code,
                      "an explicit port is used without asking whether it is his")

    def test_the_hook_does_not_bind_his_port_and_still_runs_both_sites(self):
        code = _sh(HOOK)
        self.assertNotIn("python3 control_app.py --no-open", code,
                         "the hook starts a console, which binds :17772 when that port is silent")
        self.assertNotIn("pkill", code, "the hook kills by name")
        self.assertEqual(code.count('gate_run "console-demos"'), 2,
                         "a console-demos call site was dropped or added")


RED_PROOF = [
    {
        "why": "REG-2275 - the demo no longer refuses his two ports, so 17772 is a legal target again",
        "file": "tv/demo_console.mjs",
        "find": "const HIS_PORTS = new Set([17771, 17772]);\n",
        "replace": "const HIS_PORTS = new Set([]);\n",
        "matches": 1,
    },
    {
        "why": "REG-2275 - the parent environment is spread after the private ports, so an inherited 17772 wins",
        "file": "tv/demo_console.mjs",
        "find": "    ...process.env,\n    TV_CONTROL_PORT: String(port),\n    TV_PORT: String(agent),\n",
        "replace": "    TV_CONTROL_PORT: String(port),\n    TV_PORT: String(agent),\n    ...process.env,\n",
        "matches": 1,
    },
    {
        "why": "REG-2275 - the hook starts control_app on the silent branch again, which binds :17772",
        "file": "hooks/pre-push",
        "find": "      echo \"pre-push: [$(_pp_el)] :17772 is silent — the demos boot a private console. His port is not bound.\"\n",
        "replace": "      echo \"pre-push: [$(_pp_el)] :17772 is silent — the demos boot a private console. His port is not bound.\"\n      python3 control_app.py --no-open\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
