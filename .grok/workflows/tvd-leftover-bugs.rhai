let meta = #{
    name: "tvd-leftover-bugs",
    description: "Find remaining TV DIABLO console bugs that are still live, then adversarially verify each one",
    phases: [
        #{ title: "Hunt", detail: "four read-only scanners over the console" },
        #{ title: "Verify", detail: "one skeptic per finding" },
    ],
};

let findings_schema = #{
    "type": "object", "required": ["findings"],
    "properties": #{
        "findings": #{ "type": "array", "maxItems": 6, "items": #{
            "type": "object",
            "required": ["file", "issue", "evidence"],
            "properties": #{
                "file": #{ "type": "string" },
                "issue": #{ "type": "string" },
                "evidence": #{ "type": "string" },
                "fixable": #{ "type": "boolean" },
            },
        }},
    },
};
let verdict_schema = #{
    "type": "object", "required": ["real", "reason", "evidence"],
    "properties": #{
        "real": #{ "type": "boolean" },
        "reason": #{ "type": "string" },
        "evidence": #{ "type": "string" },
    },
};

phase("Hunt");
let root = "/Users/konyo/d2r_bible_tests";
let brief_tail = "";
brief_tail += "Repo: " + root + ". TV DIABLO only: tv/control_app.py, tv/control_ui.html, tv/tv_diablo.py, tv/test_control.py, tv/test_reachability.py. ";
brief_tail += "Do NOT touch bible.html product tabs except TV receiver. Do NOT run Playwright. Cheap python/grep/read only. ";
brief_tail += "Do NOT report already-shipped REGs 124-140 or v1703 roster work as new. ";
brief_tail += "A finding needs file:line and a measurement. Empty list is valid ONLY after you grepped and read. ";
brief_tail += "Return at most 6 findings as {file, issue, evidence, fixable}.";

let jobs = [];
jobs.push(#{
    prompt: "Hunt LYING HEALTH / DEAD ROUTES / SWALLOWED FAILURES in tv/control_app.py. " + brief_tail + " Use grep and read_file. Look for except:pass on HTTP, routes that 200 with invented defaults, version stamp drift, /api that paints a stale file as live.",
    label: "hunt:control-app",
    capability_mode: "read-only",
    output_schema: findings_schema,
});
jobs.push(#{
    prompt: "Hunt PAINT / HIDDEN-PANEL / DEAD WRITER bugs in tv/control_ui.html. " + brief_tail + " The file is 1MB; search by id and function name. Known class: a panel in .hd-col is display:none on Sessions view so clicks hang. Look for remaining siblings: paint into hidden nodes, ids cloned, colours using --q-* tokens (console uses --rar-*), fallbacks that invent zeros.",
    label: "hunt:control-ui",
    capability_mode: "read-only",
    output_schema: findings_schema,
});
jobs.push(#{
    prompt: "Hunt READ/CAPTURE path bugs in tv/tv_diablo.py that would make ON AIR silently fail. " + brief_tail + " Pin must be D2R.exe only. Look for fabricated chart reads, swallow of empty OCR, wrong window pin, VERSION mismatch.",
    label: "hunt:agent",
    capability_mode: "read-only",
    output_schema: findings_schema,
});
jobs.push(#{
    prompt: "Hunt TEST/CI honesty. Read tests/v1537_read_chain_panel.spec.ts, tests/v1556_meter_coverage.spec.ts, tests/v149_tz_header_bar.spec.ts, tests/v157_set_tracker_rich_cards.spec.ts. Routine I last failed those four at 40ef6bc; later commits 816b779 and 70c514a claimed hidden-panel + v1556 premise fixes. Decide which are still PRODUCT bugs vs stale specs. " + brief_tail,
    label: "hunt:ci-delta",
    capability_mode: "read-only",
    output_schema: findings_schema,
});

let results = parallel(jobs);

let findings = [];
for r in results {
    if r != () && r.success && r.output.findings != () {
        for f in r.output.findings { findings.push(f); }
    }
}
log(findings.len().to_string() + " raw findings before verify");
if findings.len() == 0 { complete(#{ summary: "No findings from hunt.", confirmed: [] }); }

phase("Verify");
let vjobs = [];
let i = 0;
for f in findings {
    let p = "Adversarially verify this TV DIABLO finding by reading the shipped file. Default real=false unless you independently inspect the line and reproduce the measurement. Finding: " + json_encode(f) + " Repo " + root + ". No Playwright. No edits.";
    vjobs.push(#{
        prompt: p,
        label: "verify:" + i.to_string(),
        capability_mode: "read-only",
        output_schema: verdict_schema,
    });
    i += 1;
}
let verdicts = parallel(vjobs);

let confirmed = [];
let idx = 0;
for v in verdicts {
    if v != () && v.success && v.output.real == true
        && v.output.evidence != () && v.output.evidence != "" {
        confirmed.push(findings[idx]);
    }
    idx += 1;
}
log(confirmed.len().to_string() + "/" + findings.len().to_string() + " survived verification");
complete(#{ summary: confirmed.len().to_string() + " confirmed leftover TV DIABLO bugs", confirmed: confirmed, raw_n: findings.len() });
