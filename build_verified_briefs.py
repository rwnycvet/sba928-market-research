"""Generate all five verified briefs and assemble one research document."""

from pathlib import Path

from build_customer_brief import main as build_customer
from build_inventory_brief import main as build_inventory
from build_country_brief import main as build_country
from build_monthly_brief import main as build_monthly
from build_competitor_brief import main as build_competitor

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "results_v3" / "verified_reports"

BUILDERS = [
    ("customer_brief", build_customer),
    ("inventory_brief", build_inventory),
    ("country_brief", build_country),
    ("monthly_brief", build_monthly),
    ("competitor_brief", build_competitor),
]


def main():
    sections = [
        "# Retail Market Research Briefs\n\n"
        "Reporting method: Python calculations, prepared retailer "
        "summaries and fixed report templates.\n\n"
        "Measured findings, recommendations and limitations are "
        "identified in each brief. These application reports are "
        "evaluated separately from model-generated responses."
    ]

    for name, builder in BUILDERS:
        builder()

        markdown_file = OUTPUT / f"{name}.md"
        json_file = OUTPUT / f"{name}.json"

        if not markdown_file.exists() or not json_file.exists():
            raise FileNotFoundError(
                f"Missing generated report: {name}. "
                "Check the builder's OUTPUT folder."
            )

        text = markdown_file.read_text(encoding="utf-8")

        # Make each brief a section inside the combined document.
        if text.startswith("# "):
            text = "#" + text

        sections.append(text.strip())

    combined_file = OUTPUT / "retail_research_briefs.md"
    combined_file.write_text(
        "\n\n".join(sections) + "\n",
        encoding="utf-8",
    )

    print("\nAll five briefs generated.")
    print("Combined report:", combined_file)


if __name__ == "__main__":
    main()