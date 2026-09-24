# -*- coding: utf-8 -*-
"""Does a function reap its first parameter on EVERY path it can take? — read from the AST.

#177. test_no_ASSIGNED_popen_goes_unreaped (v3427) follows a Popen into a helper that reaps it,
and it trusted a helper whose first parameter was TEXTUALLY followed by `.wait(` / `.poll(` /
`target=<p>.wait`. So `if x: wp.wait()`, a reap behind `if x: return`, and a reap after a statement
in the same `try` that can raise past it all counted — the last is the v3421 defect itself, a
BrokenPipeError on `stdin.close()` that skipped the reap for three weeks.

A reap counts here only where nothing before it on the same path can leave:
  · a statement at the function's own level,
  · the FIRST statement of a try body (anything earlier in that body can raise past it),
  · anywhere in a finally,
  · the body of a with.
A reap inside an if / loop / except is conditional. An exit (return / raise) inside any of those,
before the reap, is a path that leaves unreaped. Nested defs, lambdas and classes are not the
function's own path.

Used by tv/test_control.py (the sweep) and driven by tv/test_a_conditional_reap_is_not_a_reaper.py.
It reads and decides; it runs nothing. [[source-reading-guard]]
"""
import ast

_REAP_METHODS = ("wait", "poll")
_NESTED = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
_WITH = (ast.With, ast.AsyncWith)


def _is_reap_call(node, name):
    """`name.wait(...)`, `name.poll(...)`, or anything given `target=name.wait`."""
    if not isinstance(node, ast.Call):
        return False
    f = node.func
    if (isinstance(f, ast.Attribute) and f.attr in _REAP_METHODS
            and isinstance(f.value, ast.Name) and f.value.id == name):
        return True
    for kw in node.keywords or ():
        v = kw.value
        if (kw.arg == "target" and isinstance(v, ast.Attribute) and v.attr == "wait"
                and isinstance(v.value, ast.Name) and v.value.id == name):
            return True
    return False


def _walk_own(node):
    """ast.walk that stays on this function's own path — no nested def, lambda or class."""
    todo = [node]
    while todo:
        n = todo.pop()
        yield n
        todo.extend(c for c in ast.iter_child_nodes(n) if not isinstance(c, _NESTED))


def _walk_certain(node):
    """_walk_own, minus the parts of an EXPRESSION that run on some evaluations only.

    ⚠ #235 — the second eye on 245fad4b (grok-4.7): a statement is not a branch, but an expression
    can be. `x and wp.wait()`, `x or wp.wait()` and `wp.wait() if x else None` each reap on SOME
    runs, and all three were credited as reaping on every path — so the sweep accepted a Popen handed
    to such a helper. The first operand of `and`/`or` and the TEST of `a if t else b` always run;
    the rest does not, and neither does the body of a comprehension (it may loop zero times)."""
    todo = [node]
    while todo:
        n = todo.pop()
        yield n
        if isinstance(n, ast.BoolOp):
            todo.append(n.values[0])
            continue
        if isinstance(n, ast.IfExp):
            todo.append(n.test)
            continue
        if isinstance(n, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            todo.append(n.generators[0].iter)      # the first iterable is evaluated; the body may not be
            continue
        todo.extend(c for c in ast.iter_child_nodes(n) if not isinstance(c, _NESTED))


def _reaps(stmt, name):
    return any(_is_reap_call(n, name) for n in _walk_certain(stmt))


def _exits(stmt):
    return any(isinstance(n, (ast.Return, ast.Raise)) for n in _walk_own(stmt))


def _branches(stmt):
    """A statement whose body runs on SOME paths only."""
    return not isinstance(stmt, (ast.Expr, ast.Assign, ast.AugAssign, ast.AnnAssign)) \
        and not isinstance(stmt, _WITH)


def _path(stmts, name):
    """-> 'reaped' | 'exits' | None, reading `stmts` in order as one path."""
    for st in stmts:
        if isinstance(st, (ast.Return, ast.Raise)):
            return "exits"
        if not _branches(st) and not isinstance(st, _WITH):
            if _reaps(st, name):
                return "reaped"
            continue
        if isinstance(st, _WITH):
            got = _path(st.body, name)
            if got:
                return got
            continue
        if isinstance(st, ast.Try):
            if st.body and _reaps(st.body[0], name) and not _branches(st.body[0]):
                return "reaped"
            if st.finalbody and _path(st.finalbody, name) == "reaped":
                return "reaped"
            if _exits(st):
                return "exits"
            continue
        # an if / loop / match: a reap inside is conditional; an exit inside skips what follows
        if _exits(st):
            return "exits"
    return None


def reaps_first_param(func):
    """True when `func` reaps its first positional parameter on every path. -> bool"""
    args = func.args.args
    if not args:
        return False
    return _path(func.body, args[0].arg) == "reaped"


def passes_to(call, helpers, name):
    """Is `call` one of `helpers` ({function name: its first parameter}) handed `name` as that
    parameter — positionally or by keyword, called bare or as an attribute? -> bool"""
    if not isinstance(call, ast.Call):
        return False
    f = call.func
    fname = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
    if fname not in helpers:
        return False
    if call.args:
        a = call.args[0]
        return isinstance(a, ast.Name) and a.id == name
    p0 = helpers[fname]
    return any(kw.arg == p0 and isinstance(kw.value, ast.Name) and kw.value.id == name
               for kw in call.keywords or ())
