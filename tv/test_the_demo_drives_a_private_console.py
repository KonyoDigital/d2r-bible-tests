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
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
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
        # REG-2278 — the explicit port is a hand run. Pre-push sets TV_DEMO_OWNED and must
        # not be able to reach the unowned return. The old guard required !HIS_PORTS.has,
        # which is exactly the ambient-listener path.
        i = code.find("async function demoTarget()")
        j = code.find("async function main()", i)
        fn = code[i:j]
        owned_at = fn.find("process.env.TV_DEMO_OWNED")
        port_at = fn.find("!HIS_PORTS.has(n)")
        self.assertGreaterEqual(owned_at, 0,
                                "pre-push cannot force a console this process spawned, so an "
                                "inherited TV_DEMO_PORT is adopted")
        self.assertLess(owned_at, port_at,
                        "the inherited port is considered before the pre-push owned flag")
        unowned = fn.find("owned: false")
        guard = fn.rfind("if (", 0, unowned)
        self.assertIn("!ownedRoute", fn[guard:unowned],
                      "the unowned listener is reachable while the pre-push owned flag is set")

    def test_the_hook_does_not_bind_his_port_and_still_runs_both_sites(self):
        code = _sh(HOOK)
        self.assertNotIn("python3 control_app.py --no-open", code,
                         "the hook starts a console, which binds :17772 when that port is silent")
        self.assertNotIn("pkill", code, "the hook kills by name")
        self.assertEqual(code.count('gate_run "console-demos"'), 2,
                         "a console-demos call site was dropped or added")
        # REG-2278 — both launches inherit a cleared TV_DEMO_PORT and the owned flag.
        # An ambient value must not survive into the demo the hook starts.
        cleared = code.find("unset TV_DEMO_PORT")
        arm = code.find("export TV_DEMO_OWNED=1")
        self.assertGreaterEqual(cleared, 0,
                                "pre-push leaves TV_DEMO_PORT in the environment the demo inherits")
        self.assertGreaterEqual(arm, 0,
                                "pre-push does not force the demo to spawn a console it owns")
        self.assertLess(cleared, arm, "the owned flag is set before TV_DEMO_PORT is cleared")
        launches = list(re.finditer(r'node "\$REPO/tv/demo_console\.mjs"', code))
        self.assertEqual(len(launches), 2, "both demo launches must be the owned-private route")
        for m in launches:
            self.assertLess(arm, m.start(), "a demo launch runs before the owned flag is set")
            line = code[code.rfind("\n", 0, m.start()) + 1:code.find("\n", m.start())]
            self.assertNotIn("TV_DEMO_PORT", line,
                             "a demo launch passes TV_DEMO_PORT through: %s" % line)

    def test_the_private_shelf_is_one_filmed_run_in_the_sandbox(self):
        code = _js(DEMO)
        call = "seedShelf(_sand, hist);"
        write = "fs.writeFileSync(path.join(sand, 'sessions.jsonl'),"
        still = "fs.writeFileSync(path.join(reel, 'f_' + String(k).padStart(4, '0') + '.jpg'), still);"
        self.assertEqual(code.count("function seedShelf(sand, hist) {"), 1,
                         "the private boot no longer seeds a shelf run")
        self.assertEqual(code.count(call), 1, "the seed is not what the private boot runs")
        self.assertEqual(code.count(write), 1, "the journal is not written into the sandbox")
        self.assertEqual(code.count(still), 1, "the seed no longer writes f_####.jpg stills")
        self.assertEqual(code.count("const sid = 'demo_shelf';"), 1,
                         "the seeded id changed; a reel_s_<epoch> id is hidden as a fixture")
        self.assertEqual(code.count("const reel = path.join(hist, 'reel_' + sid);"), 1)
        self.assertEqual(code.count("for (let k = 0; k < 3; k++) {"), 1,
                         "the seed no longer writes three stills, so footageN stays 0 and the card is dropped")
        self.assertEqual(code.count("sessions.jsonl"), 2,
                         "the journal path is no longer exactly the sandbox write plus the child env")
        made = code.find("fs.mkdirSync(hist, { recursive: true });")
        self.assertGreaterEqual(made, 0)
        self.assertLess(made, code.find(call), "the seed runs before its directory exists")
        self.assertLess(code.find(call), code.find(SPAWN_LINE),
                        "the child can start before the shelf run is on disk")


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
    {
        "why": "REG-2278 - pre-push can adopt an inherited listener again",
        "file": "tv/demo_console.mjs",
        "find": "  const ownedRoute = String(process.env.TV_DEMO_OWNED || '') === '1';\n"
                "  const explicit = ownedRoute ? '' : String(process.env.TV_DEMO_PORT || '').trim();\n",
        "replace": "  const explicit = String(process.env.TV_DEMO_PORT || '').trim();\n",
        "matches": 1,
    },
    {
        "why": "REG-2278 - the hook leaves TV_DEMO_PORT in the environment the demo inherits",
        "file": "hooks/pre-push",
        "find": "    unset TV_DEMO_PORT\n    export TV_DEMO_OWNED=1\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-2276 - the private boot no longer seeds a filmed run, so J7 waits on an empty shelf",
        "file": "tv/demo_console.mjs",
        "find": "  seedShelf(_sand, hist);\n",
        "replace": "",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
