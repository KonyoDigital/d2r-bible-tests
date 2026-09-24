# -*- coding: utf-8 -*-
"""HIS ANSWERS — what he said to each question the console asked him, on THIS machine's disk.

#223/#226. A row bills him only while it asks him something (console_doctor.ASKS). This is the
other half: when he answers from the mailbox, the answer is kept here and applied every time the
rows are read, so the question stops billing him and the row says what he chose — never deleted,
never hidden, and asked again when the answer lapses or the question itself changes.

  · ONE ENTRY PER QUESTION, carrying the question's fingerprint (`fp`). An answer given to one
    question can never close a different one: a new fp reopens it, and the old answer is kept as
    history, marked `stale`.
  · EFFECTS: `ruled` holds for 30 days, `snooze` for 7, `verify` for its holdMs (a physical action
    the console checks for), `handoff` moves the row to Claude's work until the question changes.
    An answer may carry its own `holdMs`.
  · UNREADABLE IS NOT EMPTY. A store that exists and will not parse is reported and NEVER written
    over — his earlier answers are worth more than a clean file. [[unknown-stays-unknown]]
  · Per machine: the path is chosen by the console (`_decision_path`), so a Windows box keeps its
    own answers to its own questions, and one machine's answers can never land on another.

Stdlib only. Writes are atomic (temp + replace).
"""
import io
import json
import os
import time

DAY_MS = 24 * 3600 * 1000
HOLD_MS = {"ruled": 30 * DAY_MS, "snooze": 7 * DAY_MS, "verify": 2 * 3600 * 1000, "handoff": None}


def load(path):
    """-> (answers dict, why). (None, why) when the store exists and cannot be read."""
    try:
        with io.open(path, encoding="utf-8") as fh:
            d = json.load(fh)
    except FileNotFoundError:
        return {}, "no answers yet"
    except Exception as e:
        return None, "the answers store exists and cannot be read (%s) - nothing will be written over it" % type(e).__name__
    if not isinstance(d, dict) or not isinstance(d.get("answers", {}), dict):
        return None, "the answers store has an unexpected shape - nothing will be written over it"
    return d.get("answers", {}), ""


def _write(path, answers):
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"v": 1, "answers": answers}, indent=1, sort_keys=True))
    os.replace(tmp, path)


def entry_for(ask, key, now_ms=None):
    """-> (entry, why). Builds the stored answer, or refuses when `key` is not one of its answers."""
    now_ms = int(now_ms if now_ms is not None else time.time() * 1000)
    ans = [a for a in (ask.get("answers") or []) if isinstance(a, dict) and a.get("key") == key]
    if not ans:
        return None, "%r is not one of the answers this question offers" % (key,)
    a = ans[0]
    hold = a.get("holdMs") if isinstance(a.get("holdMs"), int) else HOLD_MS.get(a.get("effect"))
    return {"askId": ask.get("id"), "key": key, "label": a.get("label"), "effect": a.get("effect"),
            "fp": ask.get("fp"), "at": now_ms,
            "until": (now_ms + hold) if hold else None}, ""


def record(path, ask, key, now_ms=None):
    """Store his answer to `ask`. -> (entry, why); entry None when refused (nothing written)."""
    answers, why = load(path)
    if answers is None:
        return None, why
    ent, why = entry_for(ask, key, now_ms)
    if ent is None:
        return None, why
    answers = dict(answers)
    answers[str(ask.get("id"))] = ent
    try:
        _write(path, answers)
    except Exception as e:
        return None, "the answer could not be written (%s)" % type(e).__name__
    return ent, ""


def withdraw(path, ask_id):
    """Take an answer back. -> (True|False, why)."""
    answers, why = load(path)
    if answers is None:
        return False, why
    if str(ask_id) not in answers:
        return False, "there is no answer to take back"
    answers = dict(answers)
    answers.pop(str(ask_id))
    try:
        _write(path, answers)
    except Exception as e:
        return False, "could not write (%s)" % type(e).__name__
    return True, ""


def standing(ask, answers, now_ms=None):
    """-> the stored answer that still closes `ask`, or None when the question is open."""
    if not answers:
        return None
    now_ms = int(now_ms if now_ms is not None else time.time() * 1000)
    ent = answers.get(str(ask.get("id")))
    if not isinstance(ent, dict) or ent.get("fp") != ask.get("fp"):
        return None                                     # never answered, or a different question
    until = ent.get("until")
    if isinstance(until, int) and now_ms >= until:
        return None                                     # the answer has lapsed: ask again
    return ent


def apply(rows, answers, now_ms=None):
    """Split every row's declared `asks` into `openAsks` and `answered`, in place. -> rows

    A row with no `asks` key is left alone (the partition bills it, the loud direction). A handed-off
    answer is `answered` and NOT open, so the row leaves his count and lands under Claude's work."""
    for r in rows or []:
        if not isinstance(r, dict) or "asks" not in r:
            continue
        opened, done = [], []
        for a in r.get("asks") or []:
            ent = standing(a, answers, now_ms)
            if ent is None:
                opened.append(a)
            else:
                done.append(dict(ent, q=a.get("q")))
        r["openAsks"] = opened
        r["answered"] = done
        stale = []
        for a in r.get("asks") or []:
            ent = (answers or {}).get(str(a.get("id")))
            if isinstance(ent, dict) and ent.get("fp") != a.get("fp"):
                stale.append(dict(ent, stale=True))
        if stale:
            r["staleAnswers"] = stale
    return rows
