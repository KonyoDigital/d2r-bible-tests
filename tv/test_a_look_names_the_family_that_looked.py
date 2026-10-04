# -*- coding: utf-8 -*-
"""A REAL CROSS-FAMILY LOOK MUST BE ABLE TO DISCHARGE THE DEBT IT JUST PAID.

The ledger's rule is right and stays: `family` is DERIVED, never asserted, because *"a same-family
agent writing plausible strings must never be mistakable for a cross-family look"*, and
`family_of()` returns None for anything it cannot recognise so an unattributable look fails closed.

**But a rule that fails closed on EVERYTHING closes the lane.** MEASURED 2026-09-16: v3224 and
v3225 each got a genuine Grok review through the CLI door — 6 and 12 real findings, reproduced and
acted on — and both landed as `model='' family=None`, because this Grok CLI prints no model header
and `_model_from_answer` had nothing to read. The push gate went on reporting

    second eye: v3224 OWES A LOOK — nothing was ever recorded for it

about a look that had just happened. Two eyes ran fifteen minutes each and bought nothing.

⚠⚠ THE FIX MUST NOT BECOME THE BUG IT IS FIXING. v3214-v3216 recorded `model=EYE_MODEL` — the
CONFIGURED default — regardless of who answered, so three OpenAI looks were filed `family=xai` and
the one question the ledger exists to answer was being answered from configuration. The lesson was
**read it from the evidence, not the config**.

`_model_from_transport()` is evidence: not what we hoped to run, but **which executable the
subprocess actually launched**. A same-family agent cannot produce a row through a path it never
took. That is why it derives from `EYE_CLI` and must never touch `EYE_MODEL` — and why this gate
pins that distinction rather than the string it currently returns.
[[derived-correctly-from-a-guess]] [[unknown-stays-unknown]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import second_eye_ledger as SEL
import second_eye_run as SER


class TestALookNamesTheFamilyThatLooked(unittest.TestCase):

    def _with_cli(self, path):
        real = SER.EYE_CLI
        SER.EYE_CLI = path
        self.addCleanup(setattr, SER, "EYE_CLI", real)
        return SER._model_from_transport()

    # ── THE LAW ──────────────────────────────────────────────────────────────────────────────
    def test_the_grok_cli_attributes_to_xai(self):
        m = self._with_cli("/Users/x/.grok/bin/grok")
        self.assertEqual(SEL.family_of(m), "xai",
                         "a look taken through the Grok binary could not be attributed, so it "
                         "cannot discharge a cross-family debt — which is how two real reviews "
                         "bought nothing. transport model was %r" % m)

    def test_the_codex_cli_attributes_to_openai(self):
        m = self._with_cli("/Applications/ChatGPT.app/Contents/Resources/codex")
        self.assertEqual(SEL.family_of(m), "openai",
                         "the Codex transport must name its own family too — the lane is "
                         "provider-neutral by design, and hardwiring one vendor is what made an "
                         "earlier version of it permanently empty on every machine but his")

    def test_the_claude_cli_attributes_to_anthropic(self):
        m = self._with_cli("/Users/" + "konyo/" + ".local/bin/claude")
        self.assertEqual(SEL.family_of(m), "anthropic",
                         "a look taken through the Claude binary could not be attributed, so it "
                         "cannot discharge a cross-family debt. transport model was %r" % m)

    def test_claude_is_not_handed_groks_deny_flag(self):
        real = SER.EYE_CLI
        SER.EYE_CLI = "/Users/" + "konyo/" + ".local/bin/claude"
        self.addCleanup(setattr, SER, "EYE_CLI", real)
        argv = SER._eye_argv("look")
        self.assertIn("--restricted", argv)
        self.assertIn("--output-format", argv)
        self.assertIn("--disallowedTools", argv)
        self.assertIn("Edit,Write,MultiEdit,NotebookEdit", argv)
        self.assertNotIn("--deny", argv)
        SER.EYE_CLI = "/Users/" + "x/" + ".grok/bin/grok"
        grok = SER._eye_argv("look")
        self.assertIn("--deny", grok)
        self.assertNotIn("--restricted", grok)

    def test_a_codex_binary_under_a_claude_folder_keeps_codex_flags(self):
        real = SER.EYE_CLI
        SER.EYE_CLI = "/Users/" + "claudette/" + "bin/codex"
        self.addCleanup(setattr, SER, "EYE_CLI", real)
        argv = SER._eye_argv("look")
        self.assertEqual(SER._model_from_transport(), "codex-cli")
        self.assertIn("--deny", argv)
        self.assertNotIn("--restricted", argv)

    def test_a_claude_envelope_counts_as_a_constrained_answer(self):
        raw = ('{"result": "{\\"verdict\\":\\"clean\\"}", '
               '"structured_output": {"verdict": "clean", "findings": [], "unseen": "none"}}')
        ans, structured = SER._unwrap_eye_envelope(raw)
        self.assertEqual(structured.get("verdict"), "clean")
        self.assertIn("clean", ans)
        grok = ('{"text": "all quiet", "structuredOutput": {"verdict": "findings", '
                '"findings": ["the quit still stops the service"], "unseen": ""}}')
        ans, structured = SER._unwrap_eye_envelope(grok)
        self.assertEqual(structured.get("verdict"), "findings")
        self.assertEqual(ans, "all quiet")

    def test_an_unknown_transport_stays_UNKNOWN(self):
        """⚠ Fail closed. A transport nobody recognises must not borrow a family."""
        m = self._with_cli("/usr/local/bin/some-new-eye")
        self.assertEqual(m, "", "an unrecognised binary invented an attribution: %r" % m)
        self.assertIsNone(SEL.family_of(m),
                          "UNKNOWN must stay UNKNOWN — 'some other family' is not the same claim "
                          "as 'a family I can name'")

    # ── AND IT MUST NOT BE THE OLD BUG WEARING A NEW COAT ───────────────────────────────────
    def test_the_transport_never_reads_the_configured_model(self):
        """★ v3214-v3216 filed three OpenAI looks as xai by trusting EYE_MODEL. Never again."""
        # ⚠ PARSE, DO NOT GREP. This helper's own DOCSTRING explains the EYE_MODEL bug it
        # exists to avoid, so a text search finds the word and fails on the explanation. That is
        # [[feedback-comments-vs-code]] — my own carved scar — committed inside the gate written
        # to enforce it, on the first try. ast gives the executable body only.
        import ast
        with io.open(os.path.join(HERE, "second_eye_run.py"), encoding="utf-8") as f:
            tree = ast.parse(f.read())
        fn = next((n for n in tree.body
                   if isinstance(n, ast.FunctionDef) and n.name == "_model_from_transport"), None)
        self.assertIsNotNone(fn, "the helper moved or was renamed — re-anchor this gate")
        stmts = [st for st in fn.body
                 if not (isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant)
                         and isinstance(st.value.value, str))]
        names = {n.id for st in stmts for n in ast.walk(st) if isinstance(n, ast.Name)}
        body = "\n".join(ast.dump(st) for st in stmts)
        self.assertNotIn(
            "EYE_MODEL", names,
            "_model_from_transport reads the CONFIGURED model. That is the v3214 defect exactly: "
            "a field derived correctly from a guess. It may only read EYE_CLI — which executable "
            "actually ran. Names referenced: %s" % sorted(names))
        self.assertIn("EYE_CLI", names,
                      "it must derive from the binary that was executed, or it is not evidence. "
                      "Names referenced: %s" % sorted(names))

    def test_the_answers_own_model_still_wins(self):
        """The transport is a FALLBACK. An answer that names its model is better evidence."""
        src = io.open(os.path.join(HERE, "second_eye_run.py"), encoding="utf-8").read()
        needle = "_model_from_answer(answer) or answer_model"
        self.assertEqual(
            src.count(needle), 2,
            "expected both recording sites to prefer the answer's own bytes over the passed-in "
            "model, found %d. If the precedence flips, a transport guess would override a model "
            "that named itself — and the header is the stronger evidence of the two."
            % src.count(needle))

    def test_the_cli_door_passes_the_transport(self):
        """Built on both ends and never joined is this repo's most repeated defect."""
        src = io.open(os.path.join(HERE, "second_eye_run.py"), encoding="utf-8").read()
        # ⚠ BOTH ENDS ANCHORED. This was `src[i:i + 320]` — a guess about how far the call
        # reaches, and the call grows every time somebody documents it. The ratchet in
        # test_a_source_window_must_reach_its_subject counts exactly this and I added two of them
        # in one session, in gates written to enforce careful source reading.
        # [[source-window-shortcut]] [[carved-skill-unloaded-is-unapplied]]
        i = src.find("    return record_answer(version, answer, sent, dropped")
        self.assertNotEqual(i, -1, "the CLI door's recorder call moved — re-anchor this gate")
        end = src.find("\n\n", i)
        self.assertNotEqual(end, -1, "could not find the end of the call — re-anchor this gate")
        blk = src[i:end]
        self.assertIn(
            "_model_from_transport()", blk,
            "the helper exists and the CLI door does not call it, so every look through that door "
            "is still unattributable. [[plumbing-with-no-tap]] Call site:\n%s" % blk)


RED_PROOF = [
    {
        "why": "The Claude binary is attributed. Blanking this return files the look as an "
               "unknown transport, and an unknown transport cannot discharge the debt.",
        "file": "second_eye_run.py",
        "find": "        return \"claude-cli\"        # family_of() -> anthropic\n",
        "replace": "        return \"\"\n",
        "matches": 1,
    },
    {
        "why": "Claude is launched with its own flags. Forcing the Grok branch hands Claude "
               "--deny, which that CLI rejects, so the seat stays empty.",
        "file": "second_eye_run.py",
        "find": "    if \"claude\" in low and \"grok\" not in low and \"codex\" not in low and \"chatgpt\" not in low:\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "Claude is not told to refuse file edits, so a settings change that allows tools lets the review write.",
        "file": "second_eye_run.py",
        "find": "                \"--disable-slash-commands\",\n"
                "                \"--disallowedTools\", \"Edit,Write,MultiEdit,NotebookEdit\"]\n",
        "replace": "                \"--disable-slash-commands\"]\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
