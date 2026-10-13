"""Run the whole pipeline: download -> clean -> analyse -> charts -> Tableau extract.

Usage (from the project root):  python src/run_pipeline.py
"""
import time

import analysis
import charts
import clean
import config
import download_data
import export_tableau


def main() -> None:
    start = time.time()
    for d in (config.TABLES_DIR, config.CHARTS_DIR, config.TABLEAU_DIR, config.PROCESSED_DIR):
        d.mkdir(parents=True, exist_ok=True)

    print("[0/4] download"); download_data.run()
    print("[1/4] clean + features"); df = clean.run()
    print("[2/4] analysis"); analysis.run(df)
    print("[3/4] charts"); charts.run()
    print("[4/4] tableau extract"); export_tableau.run(df)
    print(f"done in {time.time() - start:.0f}s")


if __name__ == "__main__":
    main()
