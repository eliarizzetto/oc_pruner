# ISC License
#
# Copyright (c) 2026 Elia Rizzetto
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

import argparse
import logging
from pathlib import Path
import os

from oc_validator.main import ClosureValidator
from oc_pruner import prune
from oc_pruner.config import PipelineConfig
from datetime import datetime


# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

log_dir = Path("logs")
os.makedirs("logs", exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"pipeline_{timestamp}.log"


logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def run_validation(meta_csv, cits_csv, out_dir, round_name, pipeline_config):
    """Run ClosureValidator and return report paths."""

    logging.info("Starting validation round: %s", round_name)

    cv = ClosureValidator(
        meta_in=meta_csv,
        meta_out_dir=str(out_dir / "validation_reports" / round_name / "metadata"),
        cits_in=cits_csv,
        cits_out_dir=str(out_dir / "validation_reports" / round_name / "citations"),
        strict_sequentiality=pipeline_config.strict_sequentiality,
        use_lmdb=pipeline_config.use_lmdb,
        map_size=pipeline_config.map_size,
        cache_dir=pipeline_config.cache_dir,
        meta_kwargs=pipeline_config.meta_kwargs,
        cits_kwargs=pipeline_config.cits_kwargs,
    )

    cv.validate()

    meta_csv_path = cv.meta_validator.csv_doc
    cits_csv_path = cv.cits_validator.csv_doc

    meta_report = cv.meta_validator.output_fp_json
    cits_report = cv.cits_validator.output_fp_json

    logging.info("Finished validation round: %s", round_name)

    return meta_csv_path, cits_csv_path, meta_report, cits_report


def run_pruning(csv_path, report_path, output_path, pipeline_config, verbose=False):
    """Run pruning step."""

    logging.info("Pruning CSV: %s", csv_path)

    prune(
        csv_path=csv_path,
        report_path=report_path,
        output_path=output_path,
        config=pipeline_config.pruner_config,
        verbose=verbose
    )

    logging.info("Pruned CSV written to: %s", output_path)


# ---------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------

def run_pruning_pipeline(original_fp_meta, original_fp_cits, base_out_dir, pipeline_config=None):

    if pipeline_config is None:
        pipeline_config = PipelineConfig()

    base_out_dir = Path(base_out_dir)
    cleaned_dir = base_out_dir / "cleaned"
    cleaned_dir.mkdir(parents=True, exist_ok=True)

    logging.info("Pipeline started")

    # --------------------------------------------------
    # First validation
    # --------------------------------------------------

    meta_csv, cits_csv, meta_report, cits_report = run_validation(
        original_fp_meta,
        original_fp_cits,
        base_out_dir,
        "first_round",
        pipeline_config
    )

    # --------------------------------------------------
    # First pruning
    # --------------------------------------------------

    meta_clean = cleaned_dir / Path(meta_csv).name
    cits_clean = cleaned_dir / Path(cits_csv).name

    logging.info("Starting 1st pruning round")

    run_pruning(meta_csv, meta_report, meta_clean, pipeline_config)
    run_pruning(cits_csv, cits_report, cits_clean, pipeline_config)

    # --------------------------------------------------
    # Second validation
    # --------------------------------------------------

    meta_csv, cits_csv, meta_report, cits_report = run_validation(
        meta_clean,
        cits_clean,
        base_out_dir,
        "second_round",
        pipeline_config
    )

    # --------------------------------------------------
    # Second pruning (overwrite)
    # --------------------------------------------------

    logging.info("Starting 2nd pruning round (removing potentially new errors)")

    run_pruning(meta_clean, meta_report, meta_clean, pipeline_config, verbose=True)
    run_pruning(cits_clean, cits_report, cits_clean, pipeline_config, verbose=True)

    # --------------------------------------------------
    # Third validation
    # --------------------------------------------------

    meta_csv, cits_csv, meta_report, cits_report = run_validation(
        meta_clean,
        cits_clean,
        base_out_dir,
        "third_round",
        pipeline_config
    )

    # --------------------------------------------------
    # Third pruning (overwrite)
    # --------------------------------------------------

    # 3rd pruning is necessary if the previous step has removed citation rows (linked each to 2 metadata rows)
    logging.info("Starting 3rd pruning round (final cleanup)")
    run_pruning(meta_clean, meta_report, meta_clean, pipeline_config, verbose=True)
    run_pruning(cits_clean, cits_report, cits_clean, pipeline_config, verbose=True)

    # --------------------------------------------------
    # Final validation
    # --------------------------------------------------

    logging.info("Starting final validation sanity check")

    try:

        final_cv = ClosureValidator(
            meta_in=meta_clean,
            meta_out_dir=str(base_out_dir / "validation_reports" / "final_round" / "metadata"),
            cits_in=cits_clean,
            cits_out_dir=str(base_out_dir / "validation_reports" / "final_round" / "citations"),
            strict_sequentiality=pipeline_config.strict_sequentiality,
            use_lmdb=pipeline_config.use_lmdb,
            map_size=pipeline_config.map_size,
            cache_dir=pipeline_config.cache_dir,
            meta_kwargs=pipeline_config.meta_kwargs,
            cits_kwargs=pipeline_config.cits_kwargs,
        )

        meta_result, cits_result = final_cv.validate()

        # Support both old API (returns lists) and new API (returns bools)
        if isinstance(meta_result, bool):
            meta_is_valid = meta_result
            cits_is_valid = cits_result
        else:
            meta_is_valid = not meta_result  # empty list -> True
            cits_is_valid = not cits_result

        if meta_is_valid and cits_is_valid:
            logging.info("Final validation passed with no errors")
            logging.info("Final cleaned metadata CSV: %s", meta_clean)
            logging.info("Final cleaned citations CSV: %s", cits_clean)
            print("Pruning pipeline completed successfully. Final cleaned CSVs are located at:")
            print(f"  Metadata: {meta_clean}")
            print(f"  Citations: {cits_clean}")
        else:
            logging.warning("Final validation found errors:")
            if isinstance(meta_result, bool):
                logging.warning("Metadata: not valid")
                logging.warning("Citations: not valid")
            else:
                logging.warning("Metadata: %s issues", len(meta_result))
                logging.warning("Citations: %s issues", len(cits_result))
            print("Pruning pipeline completed with validation errors. Check logs for details.")
    
    except Exception as e:
        logging.error("Error during final validation: %s", str(e))
        print("An error occurred during final validation.")
        import traceback
        traceback.print_exc()


# ---------------------------------------------------------------------
# Note: The CLI entry point is now handled by oc_pruner/cli.py
# Run with: oc_pruner pipeline -m <meta.csv> -c <citations.csv> -o <output_dir>
# ---------------------------------------------------------------------
