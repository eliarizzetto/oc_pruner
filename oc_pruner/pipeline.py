import argparse
import logging
from pathlib import Path
import os

from oc_validator.main import ClosureValidator
from oc_pruner import prune
from oc_pruner.config import PrunerConfig
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

def run_validation(meta_csv, cits_csv, out_dir, round_name):
    """Run ClosureValidator and return report paths."""
    
    logging.info("Starting validation round: %s", round_name)

    cv = ClosureValidator(
        meta_csv_doc=meta_csv,
        meta_output_dir=out_dir / "validation_reports" / round_name / "metadata",
        cits_csv_doc=cits_csv,
        cits_output_dir=out_dir / "validation_reports" / round_name / "citations",
        meta_kwargs={'verify_id_existence': False},
        cits_kwargs={'verify_id_existence': False}
    )

    cv.validate()

    meta_csv_path = cv.meta_validator.csv_doc
    cits_csv_path = cv.cits_validator.csv_doc

    meta_report = cv.meta_validator.output_fp_json
    cits_report = cv.cits_validator.output_fp_json

    logging.info("Finished validation round: %s", round_name)

    return meta_csv_path, cits_csv_path, meta_report, cits_report


def run_pruning(csv_path, report_path, output_path, verbose=False):
    """Run pruning step."""
    
    logging.info("Pruning CSV: %s", csv_path)

    config = PrunerConfig(
        error_type_filter="all",
        ignore_error_labels=[]
    )

    prune(
        csv_path=csv_path,
        report_path=report_path,
        output_path=output_path,
        config=config,
        verbose=verbose
    )

    logging.info("Pruned CSV written to: %s", output_path)


# ---------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------

def run_pruning_pipeline(original_fp_meta, original_fp_cits, base_out_dir):

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
        "first_round"
    )

    # --------------------------------------------------
    # First pruning
    # --------------------------------------------------

    meta_clean = cleaned_dir / Path(meta_csv).name
    cits_clean = cleaned_dir / Path(cits_csv).name

    logging.info("Starting 1st pruning round")

    run_pruning(meta_csv, meta_report, meta_clean)
    run_pruning(cits_csv, cits_report, cits_clean)

    # --------------------------------------------------
    # Second validation
    # --------------------------------------------------

    meta_csv, cits_csv, meta_report, cits_report = run_validation(
        meta_clean,
        cits_clean,
        base_out_dir,
        "second_round"
    )

    # --------------------------------------------------
    # Second pruning (overwrite)
    # --------------------------------------------------

    logging.info("Starting 2nd pruning round (removing potentially new errors)")

    run_pruning(meta_clean, meta_report, meta_clean, verbose=True)
    run_pruning(cits_clean, cits_report, cits_clean, verbose=True)

    # -------------------------------------------------- 
    # Third validation
    # --------------------------------------------------

    meta_csv, cits_csv, meta_report, cits_report = run_validation(
        meta_clean,
        cits_clean,
        base_out_dir,
        "third_round"
    )

    # --------------------------------------------------
    # Third pruning (overwrite)
    # --------------------------------------------------

    # 3rd pruning is necessary if the previous step has removed citation rows (linked each to 2 metadata rows)
    logging.info("Starting 3rd pruning round (final cleanup)")  
    run_pruning(meta_clean, meta_report, meta_clean, verbose=True)
    run_pruning(cits_clean, cits_report, cits_clean, verbose=True)

    # --------------------------------------------------
    # Final validation
    # --------------------------------------------------

    logging.info("Starting final validation sanity check")

    try:

        final_cv = ClosureValidator(
            meta_csv_doc=meta_clean,
            meta_output_dir=base_out_dir / "validation_reports" / "final_round" / "metadata",
            cits_csv_doc=cits_clean,
            cits_output_dir=base_out_dir / "validation_reports" / "final_round" / "citations",
            meta_kwargs={'verify_id_existence': False},
            cits_kwargs={'verify_id_existence': False}
        )

        meta_final_report, cits_final_report = final_cv.validate()

        if not meta_final_report and not cits_final_report:
            logging.info("Final validation passed with no errors")
            logging.info("Final cleaned metadata CSV: %s", meta_clean)
            logging.info("Final cleaned citations CSV: %s", cits_clean)
            print("Pruning pipeline completed successfully. Final cleaned CSVs are located at:")
            print(f"  Metadata: {meta_clean}")
            print(f"  Citations: {cits_clean}")
        else:
            logging.warning("Final validation found errors:")
            logging.warning("Metadata: %s issues", len(meta_final_report))
            logging.warning("Citations: %s issues", len(cits_final_report))
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
