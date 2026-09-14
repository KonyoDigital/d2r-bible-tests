#!/usr/bin/env python3
"""v1489 — stamp a new version across the four surfaces that carry one.

Usage: python bump_version.py v<N> <short name> <note...>   (the leading 'v' is required)

The version lives in four places: the board's `D2R_BUILD`, `control_app.py`'s `/api/status`,
`tv_diablo.py`'s `VERSION`, and `tv/WINDOWS_SHIP.json`. Bumping them by hand is four chances to
miss one, and a half-bumped tree is not cosmetic — `test_button_matrix` compares the LIVE app's
version to the ship manifest, so a missed stamp surfaces as "the running app is a different build
than the tree you are testing" and sends the next person hunting a phantom.

The board note is a SINGLE-QUOTED JS literal. Writing one by hand during v1478 put an apostrophe in
"someone else's chronicle", which terminated the string early and threw a SyntaxError that blanks
the entire 37k-line page. The syntax gate caught it — but the right place to stop that class is
before it is written, so this refuses an apostrophe outright rather than relying on the gate to
notice afterwards.

Each stamp is verified after writing: a silent no-op replace would leave the tree half-bumped,
which is the exact failure this tool exists to prevent.
"""
import ast, datetime, io, json, os, re, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# v1489 — this tool prints, so it must survive the operator's console (REG-044/054/077/078).
# Caught by TestToolsCanReportTheirVerdict on its first run, which is the gate doing its job.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from console_safe import enable as _console_safe
    _console_safe()
except Exception:
    pass


def _parses_as_js(text):
    """-> a problem string, or None. Parses `text` as a classic script with node."""
    try:
        sys.path.insert(0, os.path.join(REPO, "tv"))
        import js_syntax_gate as _js
        node = _js._node_bin()
        if not node:
            return None                       # no node: UNMEASURED, and _preflight already said so
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
            fh.write(text)
            tmp = fh.name
        try:
            r = subprocess.run([node, "--check", tmp], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=30)
            if r.returncode != 0:
                lines = (r.stderr or "").strip().splitlines()
                return next((l for l in lines if "SyntaxError" in l),
                            lines[0] if lines else "node --check exited %d" % r.returncode).strip()
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass
    except Exception as e:
        return None                            # cannot measure is not the same as broken
    return None


def _preflight(repo=None):
    """Refuse to stamp a tree that does not PARSE. Raises SystemExit; writes nothing.

    ⚠⚠ v3103 — THE CHOKE POINT HAD NO CHECK, AND I PUT A SyntaxError ON HIS SCREEN THROUGH IT.
    On 2026-09-14 a splice left a bare `} catch(e){}` in bible.html. I then ran this tool, which
    happily stamped v3100 onto a file the browser refuses to parse — and because HIS CONSOLE EXECS
    THE WORKING TREE, `window.renderSubMeter` was never assigned on his live screen until the
    second eye found it on the shipped diff. The gate that catches exactly this (`js-syntax`,
    registered in run_gates) already existed. I did not run it. A law nobody runs is a law nobody
    applied. [[carved-skill-unloaded-is-unapplied]] [[execs-the-working-tree]]

    ⚠ THIS BELONGS HERE RATHER THAN IN ANOTHER GATE. The version bump is the ONE door every change
    passes through — four stamps move together or none do — and it is the moment the tree becomes
    something he executes. The block below already promises "nothing touches disk until all four
    are known good"; until now "known good" meant only that a regex matched. Parsing is what that
    sentence was always claiming. [[the-unjoined-end]]

    ⚠ AND IT REUSES `js_syntax_gate`, never a second copy of the block extractor. One parser, one
    vocabulary. [[copy-drift]]
    """
    # ⚠ v3103b — A ROOT, BECAUSE OTHERWISE THE LAW CANNOT SEE ITS OWN DEFEAT. Two red-proofs came
    # back BLIND: disabling a check that would have PASSED anyway changes nothing observable, so
    # the only way to prove this guard can fire is to hand it a tree that is genuinely broken —
    # which means a temp copy, which means a root. [[feedback-blind-fixture-green-gate]]
    repo = repo or REPO
    bad = []
    for rel in ("tv/control_app.py", "tv/tv_diablo.py"):
        try:
            ast.parse(io.open(os.path.join(repo, rel), encoding="utf-8").read())
        except SyntaxError as e:
            bad.append("%s: %s (line %s)" % (rel, e.msg, e.lineno))
    try:
        json.load(io.open(os.path.join(repo, "tv", "WINDOWS_SHIP.json"), encoding="utf-8"))
    except Exception as e:
        bad.append("tv/WINDOWS_SHIP.json: %s" % e)
    try:
        sys.path.insert(0, os.path.join(REPO, "tv"))
        import js_syntax_gate as _js
        # ⚠ ONE PARSER, FILES FROM THE GIVEN ROOT. The module is imported once from this repo —
        # never copied — and only the root it reads from is redirected. [[copy-drift]]
        _old_root = _js.REPO
        try:
            _js.REPO = repo
            probs, why = _js.check_with_node(["bible.html"])
        finally:
            _js.REPO = _old_root
        if why:
            # ⚠ A SKIP IS NOT A PASS, and it says which half went unmeasured rather than implying
            # the file is fine. [[unknown-stays-unknown]]
            print("   \u26a0 bump preflight could NOT parse bible.html (%s) — its syntax is "
                  "UNMEASURED for this stamp, not clean" % why, flush=True)
        bad.extend(probs)
    except Exception as e:
        print("   \u26a0 bump preflight could not run the JS parser (%s) — bible.html syntax is "
              "UNMEASURED for this stamp" % type(e).__name__, flush=True)
    if bad:
        raise SystemExit(
            "refusing to stamp a tree that does not parse — NOTHING WRITTEN.\n   "
            + "\n   ".join(bad)
            + "\n   His console EXECS this working tree, so a stamped broken file is a broken "
              "console. Fix the parse error, then bump.")


def bump(ver, name, note, repo=None):
    if "'" in note or "'" in name:
        raise SystemExit("apostrophe in note/name would break the single-quoted D2R_BUILD literal")

    # 2026-08-20 — AND A NOTE MAY NOT NAME A CSS TOKEN IN CALLABLE FORM.
    #
    # v1841 fixed a chip that referenced `var(--fs-tiny)`, a token this file never defines, and then
    # DESCRIBED the fix in the build note using that exact spelling. D2R_BUILD.note is a JS string
    # literal inside bible.html, and v1733's gate strips block comments but not string literals — so
    # it read the sentence about the token as a live reference to it and stayed red. The fix
    # re-created the very defect it fixed, one line further down. [[feedback-comments-vs-code]]
    #
    # Same shape as the apostrophe above: the note is DATA that lands in a parsed file, so what it
    # may contain is a property of the file and not of the prose. Write `--fs-tiny` bare instead.
    if "var(--" in note or "var(--" in name:
        raise SystemExit(
            "the note names a CSS token in callable form (var(--x)). D2R_BUILD.note is a string "
            "literal in bible.html and v1733's token gate cannot tell it from real CSS, so this "
            "would report a token that renders as nothing. Write the token bare: --x")

    # v1613 — REFUSE A VERSION WITHOUT ITS 'v'. Every consumer of these stamps matches `v\d+`:
    # the parity tests, the ship manifest comparison, the badge. Handing this tool a bare "1613"
    # wrote four stamps that all AGREED with each other and none of which any reader could parse —
    # a half-bumped tree by a different route, and worse than a mismatch because the stamps looked
    # internally consistent. It also poisons the next run: `cur` is found by the same `v\d+`
    # pattern, so the tool could no longer find its own previous stamp to replace.
    # v1617 — WHOLE NUMBERS ONLY. Konyo: "we said version go up in whole numbers instead of
    # decimals. so fix that too". Point releases were still being accepted here, so v1616.1 and
    # v1616.2 went out before he caught it. The rule is his and it is easy to keep by hand and easy
    # to forget under momentum, which is exactly the kind of rule that belongs in the tool.
    if not re.match(r"^v\d+$", ver):
        raise SystemExit("version must be a WHOLE number like v1617, not %r — no decimals, and the "
                         "leading 'v' is required (every stamp reader matches it)" % ver)

    # ── v1617 — COMPUTE ALL FOUR, THEN WRITE ALL FOUR ────────────────────────────────────────
    # This used to write each file as it went and raise on the first stamp that did not match. Its
    # own message said "the tree would have been left half-bumped" — but by the time tv_diablo.py
    # failed, bible.html and control_app.py had ALREADY been rewritten, so the sentence described a
    # state the tool had just created rather than one it prevented. (Seen for real stamping v1617
    # over a v1616.1 tree: two files moved, two did not.)
    # Every replacement is now resolved against the ORIGINAL text first; nothing touches disk until
    # all four are known good. The failure mode becomes "nothing happened", which is recoverable.
    repo = repo or REPO
    _preflight(repo)

    today = datetime.date.today().isoformat()
    pending = []          # [(path, new_text)]

    p = os.path.join(repo, "bible.html")
    s = io.open(p, encoding="utf-8").read()
    a = s.index("  window.D2R_BUILD = { id:'")
    b = s.index("\n", a)
    # STRICT ON WHAT IT WRITES, TOLERANT OF WHAT IT FINDS. The guard above refuses to STAMP a
    # decimal, but the tree may still be HOLDING one (v1616.1 shipped before the rule landed), and a
    # tool that cannot read the version it is replacing cannot replace it.
    _m = re.search(r"id:'(v\d+(?:\.\d+)*)'", s[a:b])
    if not _m:
        raise SystemExit("could not find the current D2R_BUILD id in bible.html — nothing written")
    cur = _m.group(1)
    new_line = ("  window.D2R_BUILD = { id:'%s', name:'%s - %s', date:'%s', note:'%s' };"
                % (ver, ver, name, today, note))
    # ⚠ AND PARSE THE ONE LINE THIS TOOL ITSELF GENERATES. `note` is free text that lands inside a
    # single-quoted JS string literal; the guards above refuse an apostrophe and a callable CSS
    # token, which are the two that have bitten, but neither is a parser. This is.
    _line_problem = _parses_as_js(new_line)
    if _line_problem:
        raise SystemExit("the D2R_BUILD line this bump would write does not parse as JS — NOTHING "
                         "WRITTEN.\n   %s\n   line: %s" % (_line_problem, new_line[:200]))
    pending.append((p, s[:a] + new_line + s[b:]))

    p = os.path.join(repo, "tv", "control_app.py")
    s = io.open(p, encoding="utf-8").read()
    if s.count('"ver": "%s"' % cur) != 1:
        raise SystemExit("control_app.py stamp not found at %s — nothing written" % cur)
    pending.append((p, s.replace('"ver": "%s"' % cur, '"ver": "%s"' % ver)))

    p = os.path.join(repo, "tv", "tv_diablo.py")
    s = io.open(p, encoding="utf-8").read()
    # tolerant read here too — the trailing comment is free text, and the version may be dotted
    s2, n = re.subn(r'VERSION = "v\d+(?:\.\d+)*"   # .*',
                    'VERSION = "%s"   # %s' % (ver, name), s, count=1)
    if n != 1:
        raise SystemExit("tv_diablo.py VERSION line did not match — nothing written")
    pending.append((p, s2))

    p = os.path.join(repo, "tv", "WINDOWS_SHIP.json")
    d = json.load(io.open(p, encoding="utf-8"))
    d["ver"] = ver
    d["note"] = "%s: %s" % (ver, note)
    pending.append((p, json.dumps(d, indent=2, ensure_ascii=False) + "\n"))

    for path, text in pending:
        nl = "\n" if path.endswith(".json") else ""
        # ⚠⚠ v2712 — THIS LOOP WAS A TORN-READ GENERATOR, AND HIS CONSOLE IS THE READER.
        # `io.open(path, "w")` TRUNCATES ON OPEN, so between the truncate and the write
        # completing, the file on disk is EMPTY. bible.html is 6 MB and his console EXECS THE
        # WORKING TREE — it re-reads that file per request — so a page load landing in that
        # window parses nothing at all. [[execs-the-working-tree]]
        #
        # MEASURED, not theorised, on a 6,254,422-char copy with a reader polling concurrently:
        #     truncate-then-write   188 reads, 9 TORN (4.8%)   every torn size == 0 bytes
        #     tmp + os.replace      203 reads, 0 TORN (0.0%)
        # The torn reads were not partial parses — they were an EMPTY FILE, which is exactly the
        # symptom he described: "a panel that renders NOTHING and says nothing", unreproducible
        # afterwards because the settled tree is fine.
        #
        # os.replace() is atomic on the same filesystem, so a concurrent reader sees either the
        # whole old file or the whole new one and never a half. The repo already does this in 93
        # places; the four version stamps — the write that runs on EVERY ship — were not among
        # them. [[open-for-write-truncates-first]] [[stale-render]]
        atomic_write(path, text, nl)

    _record_ship_in_tasks(ver, name, note)

    _drop_stale_bytecode([p for p, _t in pending])

    print("%s -> %s  (%s)" % (cur, ver, name))


def atomic_write(path, text, nl=""):
    """Write `text` to `path` so a CONCURRENT READER never sees a partial file.

    ⚠⚠ v2712 — THE FOUR-STAMP WRITE WAS A TORN-READ GENERATOR, AND HIS CONSOLE IS THE READER.
    This was `io.open(path, "w", ...).write(text)`, which TRUNCATES ON OPEN. Between the truncate
    and the write completing, the file on disk is EMPTY. bible.html is 6 MB, his console EXECS THE
    WORKING TREE and re-reads it per request, so a page load landing in that window parses nothing
    at all. [[execs-the-working-tree]]

    MEASURED on a 6,254,422-char copy with a reader polling concurrently — not theorised:

        truncate-then-write    188 reads,  9 TORN  (4.8%)   every torn size == 0 bytes
        tmp + os.replace       203 reads,  0 TORN  (0.0%)

    The torn reads were not partial parses. They were an EMPTY FILE, which is precisely the symptom
    he reported: "a panel that renders NOTHING and says nothing", unreproducible afterwards because
    the settled tree is fine. Every attempt to reproduce it on a settled tree was measuring the
    wrong moment. [[feedback-blind-fixture-green-gate]]

    os.replace() is atomic on the same filesystem: a reader sees the whole old file or the whole
    new one, never a half. The repo already did this in 93 places — the one write that runs on
    EVERY ship was not among them. [[open-for-write-truncates-first]] [[stale-render]]

    ⚠ THIS IS PER-FILE, NOT ACROSS THE FOUR. A crash between two stamps still leaves the set
    disagreeing; that is a different defect and this does not fix it. Saying otherwise would be
    the overclaim this repo keeps carving. [[unknown-stays-unknown]]

    ⚠⚠ v2795 — THIS SILENTLY DISABLED THE ENTIRE PRE-PUSH GATE, AND THE PUSH SAID SO IN A HINT
    NOBODY WOULD HAVE READ TWICE. `os.replace` moves the TEMP FILE's inode into place, and the temp
    file is created with the default 0644 — so every executable this function touched came out
    NON-EXECUTABLE. Measured 2026-09-08: `hooks/pre-push` was 100755 at v2793 and 100644 at v2794,
    and git printed

        hint: The 'hooks/pre-push' hook was ignored because it's not set as executable.

    then pushed straight to origin with NO gates at all — no test_control, no render, no smoke, no
    second eye. The atomicity fix and the mode loss are the same line: preserving the CONTENT while
    dropping the PERMISSION is not preserving the file. [[the-unjoined-end]]

    ⚠⚠ v2797 — AND THE v2795 FIX LEFT A WINDOW, FOUND BY A COLD CROSS-FAMILY REVIEW OF THE
    SHIPPED BYTES. v2795 restored the mode by chmod'ing AFTER os.replace. Between those two calls
    the new content is already live under the TEMP FILE's mode, which is born under umask.
    MEASURED, stopping the sequence mid-way:

        target before         0o755
        the temp file's mode  0o644   <- born under umask
        AFTER os.replace      0o644   <- the window
        after os.chmod        0o755

    For `hooks/pre-push` that window IS THE ORIGINAL DEFECT IN MINIATURE: a push starting inside it
    sees a non-executable hook and skips every gate. Not hypothetical here — pushes run in the
    background while other work continues. Reproduced before being believed.

    ⇒ THE MODE GOES ON THE TEMP FILE, BEFORE THE REPLACE, so the final inode appears with its
    content and its permissions in ONE atomic step. The post-replace chmod survives only as a
    fallback for the case where that pre-chmod itself failed.

    ⚠ AND THE TEMP NAME IS UNIQUE NOW. `path + ".tmp"` is deterministic, so two writers on one path
    silently truncate each other's temp file — bump_version writes four stamps and this session
    routinely runs things concurrently. mkstemp in the SAME directory keeps the rename atomic; a
    cross-filesystem rename is not.

    ⚠ NOT CLAIMED: durability. The same review noted there is no fsync of the file or its parent
    directory, so a crash after the replace can leave the entry pointing at unflushed data. That is
    TRUE and is not fixed here — this function's contract is "no torn read", not "survives power
    loss". Saying so beats implying otherwise. [[unknown-stays-unknown]]

    A file that did not exist has no mode to copy and correctly keeps the default.
    """
    try:
        _mode = os.stat(path).st_mode
    except OSError:
        _mode = None
    _dir = os.path.dirname(os.path.abspath(path)) or "."
    _fd, tmp = tempfile.mkstemp(prefix=os.path.basename(path) + ".", suffix=".tmp", dir=_dir)
    os.close(_fd)
    try:
        with io.open(tmp, "w", encoding="utf-8", newline=nl) as fh:
            fh.write(text)
        # ⛔ BEFORE the replace — the whole point of the v2797 correction.
        # ⚠ AND THE NEW-FILE CASE CHANGED UNDER ME: mkstemp creates 0600, where the old
        #   io.open(path,"w") produced 0666 & ~umask (0644 here). Caught by PRINTING the number
        #   rather than assuming the swap was mode-neutral — a brand-new generated file readable
        #   only by its owner would break anything else on this machine that reads it. So a file
        #   with no previous mode gets the umask default it would always have had.
        try:
            if _mode is not None:
                os.chmod(tmp, _mode & 0o7777)
            else:
                _um = os.umask(0)
                os.umask(_um)
                os.chmod(tmp, 0o666 & ~_um)
        except OSError:
            pass
        os.replace(tmp, path)
    except BaseException:
        # a failed write must not leave a stray temp beside his files
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    if _mode is not None and (os.stat(path).st_mode & 0o7777) != (_mode & 0o7777):
        try:
            os.chmod(path, _mode & 0o7777)   # fallback: the pre-chmod did not take
        except OSError:
            pass


def _record_ship_in_tasks(ver, name, note):
    """Write the ship's row into TASKS.md, because remembering to has failed THREE times.

    TASKS.md documents the workflow in its own words: **bump -> record the row here -> commit**,
    and adds that "the gate fails on its own ship if that middle step is skipped - it did, on
    v2670, which is how this line came to exist."

    It then happened again on v2712, v2713 AND v2714, in one session, by the same hand that had
    just read that sentence. `test_tasks_ships_are_recorded` caught it in CI, correctly, three
    ships late.

    ⚠ THE FIX IS NOT TO REMEMBER HARDER. A step that a human (or a model) must remember, in the
    middle of a mechanical sequence the machine is already performing, will be skipped again. The
    bump already edits four files; the list is the fifth surface describing the same event, and
    the tool that moves the stamp is the only thing that reliably knows a ship happened.
    [[the-unjoined-end]] [[copy-drift]]

    Never fatal: a bump that cannot write the list must still bump. A version stamp half-applied
    because a MARKDOWN TABLE could not be edited would be a far worse failure than the one this
    prevents.
    """
    try:
        p = os.path.join(REPO, "TASKS.md")
        s = io.open(p, encoding="utf-8").read()
        if ver in s:
            return                              # already recorded by hand; do not duplicate
        # the newest row sits directly under the table header, so anchor on the header itself
        # rather than on whatever version happens to be top today.
        head = "| version | commit | commit subject |\n|---|---|---|\n"
        if head not in s:
            print("   \u26a0 TASKS.md ship table not found - record %s by hand" % ver)
            return
        row = "| **%s** | `(this commit)` | %s \u2014 %s |\n" % (ver, ver, (note or name or "").strip())
        io.open(p, "w", encoding="utf-8").write(s.replace(head, head + row, 1))
        print("   recorded %s in TASKS.md" % ver)
        # ⚠⚠ AFTER THE WRITE, NOT BEFORE — AND THAT ORDER IS THE WHOLE FIX.
        # v2927 put this block ABOVE the write. `s` was read at the top of this function, the
        # stamper then wrote TASKS.md itself, and the line above wrote STALE `s` straight back over
        # it. MEASURED 2026-09-11: the v2928 bump printed "bound 1 version row(s)" and commit
        # 6442cfe5 still carries `| **v2927** | \u0060(this commit)\u0060 |`. The backfill was
        # real, correct, and clobbered in the same breath — a lost update.
        # ⚠ AND THE LAW WAS HOLLOW. test_bump_version_actually_CALLS_the_stamper asserted the
        # import and the .stamp() call existed, so it proved the tap was PLUMBED and never that
        # water came out. It cites [[plumbing-with-no-tap]] in its own docstring.
        # being written — at bump time the commit genuinely does not exist — but nothing ever came
        # back to replace it, and MEASURED 2026-09-11 that left 249 of 278 rows unable to bind a
        # version to a commit at all. Grok Bot raised it three ticks running (GB-B-403/404/405).
        # The previous version's commit DOES exist by now, so every row but the newest can be
        # bound here. [[the-unjoined-end]] [[plumbing-with-no-tap]]
        try:
            import stamp_versions as _sv
            _r = _sv.stamp()
            _c = _r["counts"]
            # ⚠⚠ v2936 — A REFUSAL IS A RETURN VALUE, NOT AN EXCEPTION, AND THE `except` BELOW
            # CANNOT SEE IT. v2931 taught stamp() to refuse when `git log` cannot be asked; main()
            # was joined to that and THIS caller was not, so the condition below (all zeros on a
            # refusal) was False and the bump printed only "recorded vNNNN in TASKS.md".
            # MEASURED: with git unreachable, stamp() returned a `why` and this path said nothing.
            # The instrument failure v2931 exists to announce was silent on the one path that runs
            # at every bump — REG-936's own shape, one caller over.
            # [[the-unjoined-end]] [[feedback-silence-is-not-evidence]]
            if _r.get("why"):
                print("   \u26a0 version rows were NOT backfilled: %s" % _r["why"])
            elif _c["bound"] or _c["carried"] or _c["unknown"]:
                print("   bound %d version row(s) to a commit (%d carried, %d UNKNOWN)"
                      % (_c["bound"], _c["carried"], _c["unknown"]))
        except Exception as _e:
            # ⚠ SAY SO. A silent failure here is how the table quietly goes back to 249 unbound
            # rows with everything looking healthy. [[feedback-silence-is-not-evidence]]
            print("   ⚠ version rows were NOT backfilled (%s) — run tv/stamp_versions.py by hand"
                  % type(_e).__name__)
    except Exception as e:
        print("   \u26a0 could not record %s in TASKS.md (%s) - do it by hand" % (ver, str(e)[:80]))


def _drop_stale_bytecode(paths):
    """Delete the cached .pyc for every source this bump just edited.

    ⚠ THIS BUMP'S EDITS ARE INHERENTLY LENGTH-PRESERVING. "v2366" -> "v2367" is the same byte
    count, and Python decides a .pyc is fresh from the source's mtime AND SIZE. Edit twice inside
    one filesystem-timestamp tick and the interpreter keeps running the OLD compiled constants
    against correct source - silently.

    It bit three times on 2026-09-01 alone. The worst was `_app_ver()`, which deliberately reads
    the version out of `status_payload.__code__.co_consts` so it reports what this process is
    RUNNING rather than what is on disk (v2155). With a stale .pyc it answered v2366 while the
    file said v2367, `test_app_ver_equals_ship_version` went red on a correct tree, and a push
    was blocked twice for a defect that did not exist.

    ⚠ AND THE CACHE IS NOT IN __pycache__ ON THIS MAC. `sys.pycache_prefix` relocates it to
    ~/Library/Caches/com.apple.python/<absolute source path>, so anyone deleting __pycache__ and
    concluding "cleared" has cleared nothing. Both locations are removed here.
    [[python-pycache-prefix-mac]]
    """
    import sys as _sys
    removed = []
    for src in paths:
        if not src.endswith(".py"):
            continue
        stem = os.path.basename(src)[:-3]
        cands = []
        prefix = getattr(_sys, "pycache_prefix", None)
        if prefix:
            cands.append(os.path.join(prefix + os.path.dirname(os.path.abspath(src))))
        cands.append(os.path.join(os.path.dirname(os.path.abspath(src)), "__pycache__"))
        for d in cands:
            try:
                if not os.path.isdir(d):
                    continue
                for f in os.listdir(d):
                    if f.startswith(stem + ".") and f.endswith(".pyc"):
                        os.remove(os.path.join(d, f))
                        removed.append(f)
            except Exception:
                pass          # a cache we cannot clear is a warning, never a failed bump
    if removed:
        print("   cleared %d stale .pyc: %s" % (len(removed), ", ".join(sorted(set(removed))[:4])))
    return removed


def _regen_blueprint():
    """BLUEPRINT.md is GENERATED from the code, so a version bump must regenerate it.

    ⚠⚠ MEASURED 2026-09-10: the pre-push gate refused THREE separate pushes in one session with
    "BLUEPRINT.md no longer matches the code" — every time because a version had added or removed a
    gate and the generated map still carried the old count. Each refusal cost a full push cycle:
    the second eye, the blueprint check, the suites, all re-run from the top.

    The gate is RIGHT to refuse and must not regenerate the map itself — the pre-push grades the
    WORKING TREE, so a hook that edits the tree mid-run is grading bytes it just changed. The place
    to do it is HERE, at the bump, where the tree is already being written on purpose.

    ⚠ A FAILURE HERE MUST NEVER FAIL THE BUMP. The four stamps are the ship; the map is a
    convenience. If it cannot regenerate, say so and let the pre-push refuse — that is the gate
    doing its job, not a reason to lose a version stamp.
    """
    import subprocess
    here = os.path.dirname(os.path.abspath(__file__))
    try:
        r = subprocess.run([sys.executable, os.path.join(here, "blueprint.py")],
                           capture_output=True, text=True, timeout=120)
        if r.returncode == 0:
            print("   regenerated BLUEPRINT.md")
            return True
        print("   ⚠ BLUEPRINT.md could NOT be regenerated (exit %s) — the pre-push will refuse "
              "until it is: python3 tv/blueprint.py" % r.returncode)
    except Exception as exc:
        print("   ⚠ BLUEPRINT.md regeneration raised %s — run python3 tv/blueprint.py by hand"
              % type(exc).__name__)
    return False


if __name__ == "__main__":
    bump(sys.argv[1], sys.argv[2], " ".join(sys.argv[3:]))
    _regen_blueprint()
