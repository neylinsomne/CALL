"""
Pipeline Orchestrator
=====================
CLI for running the voice distillation pipeline stages.

Usage:
    python run_pipeline.py --stage all --reference-audio voice.wav
    python run_pipeline.py --stage reference --tts-url http://tts:8001
    python run_pipeline.py --stage evolve --steps 10000
    python run_pipeline.py --stage validate
"""

import argparse
import asyncio
import json
import shutil
import time
import uuid
from pathlib import Path

from loguru import logger

from config import (
    BASE_DIR, REFERENCE_DIR, EVOLVED_DIR, VALIDATION_DIR, RUNS_DIR,
    TTS_URL, STYLES, WALK_STEPS,
)


def setup_logging(run_dir: Path):
    """Configure logging for a pipeline run."""
    log_path = run_dir / "pipeline.log"
    logger.add(str(log_path), rotation="50 MB", level="INFO")


def save_state(run_dir: Path, state: dict):
    """Save pipeline state for resume support."""
    state_path = run_dir / "state.json"
    state_path.write_text(json.dumps(state, indent=2, default=str))


def load_state(run_dir: Path) -> dict:
    """Load pipeline state if it exists."""
    state_path = run_dir / "state.json"
    if state_path.exists():
        return json.loads(state_path.read_text())
    return {}


async def run_reference_stage(args, run_dir: Path) -> dict:
    """Stage 1: Generate F5-TTS reference audio."""
    from reference_generator import run_stage

    logger.info("="*60)
    logger.info("STAGE 1: Reference Generation (F5-TTS)")
    logger.info("="*60)

    results = await run_stage(
        source_audio=args.reference_audio,
        source_text=args.reference_text,
        tts_url=args.tts_url,
        output_dir=Path(args.output_dir) / "reference_audio",
    )

    return {
        "stage": "reference",
        "completed": True,
        "styles_generated": list(results.keys()),
        "paths": {k: str(v) for k, v in results.items()},
    }


def run_evolve_stage(args, run_dir: Path) -> dict:
    """Stage 2: Evolve Kokoro voice tensors."""
    import asyncio
    from voice_evolver import run_stage

    logger.info("="*60)
    logger.info("STAGE 2: Voice Evolution (KVoiceWalk)")
    logger.info("="*60)

    ref_dir = Path(args.output_dir) / "reference_audio"
    evolved_dir = Path(args.output_dir) / "evolved_voices"

    results = asyncio.run(run_stage(
        reference_dir=ref_dir,
        output_dir=evolved_dir,
        styles=args.styles,
        walk_steps=args.steps,
        use_interpolation=not args.no_interpolation,
    ))

    return {
        "stage": "evolve",
        "completed": True,
        "styles_evolved": list(results.keys()),
        "paths": {k: str(v) for k, v in results.items()},
    }


def run_validate_stage(args, run_dir: Path) -> dict:
    """Stage 3: Validate evolved voices."""
    from voice_validator import run_stage

    logger.info("="*60)
    logger.info("STAGE 3: Voice Validation")
    logger.info("="*60)

    ref_dir = Path(args.output_dir) / "reference_audio"
    evolved_dir = Path(args.output_dir) / "evolved_voices"
    val_dir = Path(args.output_dir) / "validation"

    reports = run_stage(ref_dir, evolved_dir, val_dir)

    valid_styles = [s for s, r in reports.items() if r.get("valid")]
    invalid_styles = [s for s, r in reports.items() if not r.get("valid")]

    if invalid_styles:
        logger.warning(f"Invalid styles: {invalid_styles}")
    if valid_styles:
        logger.info(f"Valid styles: {valid_styles}")

    return {
        "stage": "validate",
        "completed": True,
        "valid_styles": valid_styles,
        "invalid_styles": invalid_styles,
        "reports": {k: {"valid": v.get("valid"), "speaker_sim": v.get("speaker_similarity", {}).get("mean", 0)} for k, v in reports.items()},
    }


def run_deploy_stage(args, run_dir: Path) -> dict:
    """Stage 4: Deploy evolved voices for production use."""
    logger.info("="*60)
    logger.info("STAGE 4: Deploy")
    logger.info("="*60)

    evolved_dir = Path(args.output_dir) / "evolved_voices"
    deploy_dir = Path("/data/models/kokoro_voices") if Path("/data/models").exists() else evolved_dir

    if deploy_dir != evolved_dir:
        deploy_dir.mkdir(parents=True, exist_ok=True)
        for pt_file in evolved_dir.glob("*.pt"):
            dest = deploy_dir / pt_file.name
            shutil.copy2(pt_file, dest)
            logger.info(f"Deployed: {pt_file.name} -> {dest}")

    logger.info(
        "\nTo activate Kokoro as TTS backend:\n"
        "  1. Set TTS_BACKEND=kokoro in .env\n"
        "  2. Set KOKORO_VOICE_PATH to the tensor directory\n"
        "  3. Restart the TTS service: docker compose restart tts\n"
    )

    return {
        "stage": "deploy",
        "completed": True,
        "voices_dir": str(deploy_dir),
        "available_voices": [f.stem for f in evolved_dir.glob("*.pt")],
    }


async def run_pipeline(args):
    """Run the complete pipeline or individual stages."""
    # Setup run directory
    run_id = str(uuid.uuid4())[:8]
    run_dir = RUNS_DIR / f"run_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(run_dir)

    logger.info(f"Pipeline run: {run_id}")
    logger.info(f"Output dir: {args.output_dir}")
    logger.info(f"Stage: {args.stage}")

    start_time = time.time()
    state = {"run_id": run_id, "start_time": start_time, "stages": {}}

    stages_to_run = []
    if args.stage == "all":
        stages_to_run = ["reference", "evolve", "validate", "deploy"]
    else:
        stages_to_run = [args.stage]

    for stage in stages_to_run:
        logger.info(f"\n>>> Running stage: {stage}")
        stage_start = time.time()

        try:
            if stage == "reference":
                result = await run_reference_stage(args, run_dir)
            elif stage == "evolve":
                result = run_evolve_stage(args, run_dir)
            elif stage == "validate":
                result = run_validate_stage(args, run_dir)
            elif stage == "deploy":
                result = run_deploy_stage(args, run_dir)
            else:
                logger.error(f"Unknown stage: {stage}")
                continue

            result["elapsed_seconds"] = time.time() - stage_start
            state["stages"][stage] = result
            save_state(run_dir, state)

            logger.info(f"<<< Stage '{stage}' completed ({result['elapsed_seconds']:.1f}s)")

        except Exception as e:
            logger.error(f"Stage '{stage}' failed: {e}")
            state["stages"][stage] = {
                "stage": stage,
                "completed": False,
                "error": str(e),
            }
            save_state(run_dir, state)
            if args.stage == "all":
                logger.error("Stopping pipeline due to stage failure.")
                break

    # Final summary
    total_time = time.time() - start_time
    state["total_elapsed_seconds"] = total_time
    save_state(run_dir, state)

    logger.info(f"\n{'='*60}")
    logger.info(f"Pipeline completed in {total_time:.1f}s ({total_time/60:.1f}min)")
    logger.info(f"Run directory: {run_dir}")
    logger.info(f"State file: {run_dir / 'state.json'}")

    for stage_name, stage_result in state.get("stages", {}).items():
        status = "OK" if stage_result.get("completed") else "FAILED"
        logger.info(f"  [{status}] {stage_name}")

    logger.info(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Voice Distillation Pipeline: F5-TTS -> Kokoro via KVoiceWalk",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline
  python run_pipeline.py --stage all --reference-audio /path/to/voice.wav

  # Individual stages
  python run_pipeline.py --stage reference --tts-url http://tts:8001
  python run_pipeline.py --stage evolve --steps 5000
  python run_pipeline.py --stage validate
  python run_pipeline.py --stage deploy

  # Quick test (100 steps)
  python run_pipeline.py --stage evolve --steps 100 --styles neutral
        """,
    )

    parser.add_argument(
        "--stage",
        choices=["all", "reference", "evolve", "validate", "deploy"],
        default="all",
        help="Pipeline stage to run",
    )
    parser.add_argument("--reference-audio", help="Source voice audio file (WAV)")
    parser.add_argument("--reference-text", help="Transcript of the source audio")
    parser.add_argument("--tts-url", default=TTS_URL, help="F5-TTS service URL")
    parser.add_argument("--output-dir", default=str(BASE_DIR), help="Output directory")
    parser.add_argument("--steps", type=int, default=WALK_STEPS, help="Random walk steps")
    parser.add_argument("--styles", nargs="+", help="Specific styles to process")
    parser.add_argument("--no-interpolation", action="store_true", help="Skip interpolation search")

    args = parser.parse_args()

    # Ensure output directories exist
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    asyncio.run(run_pipeline(args))


if __name__ == "__main__":
    main()
