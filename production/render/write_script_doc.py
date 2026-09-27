"""Generate the narration script document (with timecodes) from the narration timelines."""
import json
from pathlib import Path

import video_core as vc

ON_SCREEN = {
    "hook": "A tax incentive can improve your return. / Can it fix a weak location? — four facades rise; the street goes quiet around the one carrying a 'Tax incentive' tag",
    "promise": "El Salvador Tax Incentives — Who qualifies for up to 10 years of relief? — 01 Who qualifies · 02 Who actually benefits · 03 What's left after location and execution costs",
    "opportunity": "Hero numeral counts 1→10 'years' with a reader seated on it and a ten-dot ruler; orange block map of the defined Historic Center (illustrative); 'Separate nationwide regimes' (Tourism, Free zones, International services); 'Not every business qualifies. Verify current law and regulation before underwriting.'",
    "checks": "Giant 3 'checks before you model any benefit': 1 Exact location (inside vs. one block outside) · 2 Qualifying investment (Food, Lodging, Culture, Housing, Restoration; tape-measure vs. minimum threshold) · 3 Approval (APLAN · Ventanilla Única; 'Qualified' stamp; 'No approval, no benefit to model.')",
    "beneficiary": "Which entity receives the benefit? — Owner · landlord / Operator · tenant / Developer; 'Landlord qualified ≠ tenant benefits automatically'",
    "economics": "Simplified hypothetical · annual, after tax: $30,000 − $24,000 = $6,000 as hero numerals; flat waterfall chart; 'Excludes other cost, timing, and risk differences. Not a calculation of Salvadoran tax liability. Not a promised return.'",
    "execution": "Execution still decides the outcome — 01 Demand, 02 Permits, 03 Utilities, 04 Opening delays; eroding advantage bar / Underwrite in two layers — 1 Base case (no incentives) · 2 Qualified benefit (striped, subject to approval)",
    "services": "How Aurora helps — From market entry to operating launch: 01 Verify eligibility · 02 Test the site · 03 Model the real cost to open",
    "close": "Aurora lockup; Understand the incentive. / Underwrite the opportunity. / Subscribe to @ConAurora; The economics behind expansion, not just the headline incentives; Next episode card",
    "s_hook": "Up to 10 years of tax relief. Does your project qualify? (counting numeral with seated reader)",
    "s_zone": "San Salvador's Historic Center · Within the defined area (orange block map, illustrative)",
    "s_checks": "Before you count the savings: Location · Investment · Approval",
    "s_benef": "Who receives the benefit? Owner · Operator · Developer; A landlord's approval does not automatically extend to the tenant.",
    "s_close": "Understand the incentive. / Underwrite the opportunity. / Subscribe to @ConAurora; Next breakdown: Who actually gets the benefit?",
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
