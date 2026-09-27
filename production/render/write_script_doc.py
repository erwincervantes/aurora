"""Generate the narration script document (with timecodes) from the narration timelines."""
import json
from pathlib import Path

import video_core as vc

ON_SCREEN = {
    "hook": "A tax incentive can improve your return. / Can it fix a weak location? — historic facade; street empties; 'Tax incentive' tag",
    "promise": "El Salvador Tax Incentives — Who qualifies for up to 10 years of relief? — three panels: which incentive applies · who receives the benefit · what remains after location and execution costs",
    "opportunity": "Up to 10 years of income-tax relief — 10-year bar; illustrative city plan with defined perimeter; 'Nationwide regimes · separate rules' (Tourism, Free zones, International services); 'Not every business qualifies. Verify current law and regulation before underwriting.'",
    "checks": "Three checks: 1 Exact location (inside vs. one block outside) · 2 Qualifying investment (Food, Lodging, Culture, Housing, Restoration; investment vs. minimum threshold) · 3 Approval (APLAN · Ventanilla Única; 'Qualified' stamp; 'No approval, no benefit to model.')",
    "beneficiary": "Which entity receives the benefit? — Owner · landlord / Operator · tenant / Developer; 'Landlord qualified ≠ tenant benefits automatically'",
    "economics": "Simplified hypothetical · Annual after-tax comparison: $30,000 − $24,000 = $6,000; waterfall chart; 'Excludes other cost, timing, and risk differences. Not a calculation of Salvadoran tax liability. Not a promised return.'",
    "execution": "Execution still decides the outcome — Demand, Permits, Utilities, Opening delays; eroding advantage bar / Underwrite in two layers — 1 Base case (no incentives) · 2 Qualified benefit (shown separately, subject to approval)",
    "close": "Aurora — Latin America Expansion; Subscribe; @ConAurora · conaurora.com; Next episode: Who receives the benefit: the owner, operator, or developer?",
    "s_hook": "Up to 10 years of tax relief? — Qualifying investments: Potentially / Every business: No",
    "s_zone": "One defined Historic Center, not the whole country — illustrative perimeter",
    "s_checks": "Three checks: Location · Investment · Approval (APLAN)",
    "s_benef": "Who receives it? — Owner · landlord ✓ / Operator · tenant ✗ / Developer ? — 'Landlord approved ≠ tenant benefits automatically'",
    "s_close": "Aurora; Subscribe; @ConAurora; Next breakdown: Who actually gets the benefit: owner, operator, or developer?",
}


def timecode(seconds):
    return f"{int(seconds // 60):d}:{seconds % 60:05.2f}"


def section(video_id, title):
    script = json.loads((vc.PRODUCTION / "script" / f"{video_id}_script.json").read_text())
    timeline = vc.load_timeline(video_id)
    words = sum(len(line["text"].split()) for scene in timeline["scenes"] for line in scene["lines"])
    voice = script["voice"]
    out = [f"## {title}", "",
           f"Runtime {timeline['duration']:.2f} s · {words} words · voice: {voice['model']}, speaker `{voice['speaker']}`, speed {voice['speed']}", "",
           "| Timecode | Scene | Narration | On screen |", "|---|---|---|---|"]
    for scene in timeline["scenes"]:
        for i, line in enumerate(scene["lines"]):
            on_screen = ON_SCREEN.get(scene["id"], "") if i == 0 else ""
            out.append(f"| {timecode(line['start'])}–{timecode(line['end'])} | {scene['id'] if i == 0 else ''} | {line['text']} | {on_screen} |")
    return "\n".join(out) + "\n"


def main():
    doc = ["# Aurora — Narration Script", "",
           "**El Salvador Tax Incentives: Who Qualifies for Up to 10 Years of Relief?**", "",
           "Channel: Aurora Latin America Expansion · @ConAurora · https://conaurora.com", "",
           "Timecodes are the exact spoken spans in the final narration (from `production/script/*_timeline.json`).", "",
           section("main", "YouTube video (1920×1080)"), section("short", "YouTube Short (1080×1920)")]
    path = vc.PRODUCTION.parent / "deliverables" / "Aurora_ElSalvador_TaxIncentives_Narration_Script.md"
    path.write_text("\n".join(doc), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
