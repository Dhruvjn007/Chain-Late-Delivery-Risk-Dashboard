"""Step 0: download the DataCo dataset from Kaggle into data/raw/ (skipped if present)."""
import io
import urllib.request
import zipfile

import config

WANTED = ["DataCoSupplyChainDataset.csv", "DescriptionDataCoSupplyChain.csv"]


def run() -> None:
    if config.RAW_FILE.exists():
        print(f"  found  {config.RAW_FILE.name}, skipping download")
        return
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    print("  downloading DataCo dataset from Kaggle (~27 MB zipped)...")
    with urllib.request.urlopen(config.KAGGLE_URL) as resp:
        archive = zipfile.ZipFile(io.BytesIO(resp.read()))
    for name in WANTED:
        archive.extract(name, config.RAW_DIR)
        print(f"  wrote  {name}")


if __name__ == "__main__":
    run()
