"""
Cohort upload API — handles DNA file uploads and persona generation.
"""

from __future__ import annotations

import uuid
from flask import Blueprint, request, jsonify, current_app

from app.services.genomics.parsers import parse_genome_file, parse_cohort_file
from app.services.genomics.persona_generator import (
    build_persona,
    build_cohort_personas,
    generate_synthetic_cohort,
)
from app.utils.logger import get_logger

cohort_bp = Blueprint("cohort", __name__)
logger = get_logger("genomicswarm.api.cohort")

# In-memory cohort store
_cohorts: dict = {}


@cohort_bp.route("/upload", methods=["POST"])
def upload_cohort():
    """
    Upload a single 23andMe/VCF file or a multi-sample VCF cohort.
    Returns cohort_id and summary.

    Form fields:
      - file: the DNA file
      - drug: drug name (e.g. "codeine")
      - dose_mg: float
      - cohort_type: "single" | "multi" (default: "single")
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Empty filename"}), 400

    drug = request.form.get("drug", "codeine")
    dose_mg = float(request.form.get("dose_mg", 30.0))
    cohort_type = request.form.get("cohort_type", "single")

    file_bytes = f.read()
    filename = f.filename

    try:
        if cohort_type == "multi":
            genomes, meta = parse_cohort_file(filename, file_bytes)
        else:
            genome, meta = parse_genome_file(filename, file_bytes)
            sample_id = meta.get("sample_id") or filename.split(".")[0]
            genomes = {sample_id: genome}

        max_agents = current_app.config.get("MAX_AGENTS", 1000)
        personas = build_cohort_personas(genomes, drug, dose_mg, max_agents=max_agents)

        cohort_id = str(uuid.uuid4())
        _cohorts[cohort_id] = {
            "id": cohort_id,
            "filename": filename,
            "drug": drug,
            "dose_mg": dose_mg,
            "personas": personas,
            "sample_count": len(personas),
            "metadata": meta,
        }

        logger.info(f"Cohort {cohort_id}: {len(personas)} personas from '{filename}'")
        return jsonify({
            "cohort_id": cohort_id,
            "sample_count": len(personas),
            "drug": drug,
            "dose_mg": dose_mg,
            "metadata": meta,
            "preview": personas[:3] if personas else [],
        }), 201

    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({"error": str(e)}), 500


@cohort_bp.route("/synthetic", methods=["POST"])
def create_synthetic_cohort():
    """
    Generate a synthetic cohort using population allele frequencies.
    Body JSON: { drug, dose_mg, n_agents, population, seed? }
    """
    data = request.get_json() or {}
    drug = data.get("drug", "codeine")
    dose_mg = float(data.get("dose_mg", 30.0))
    n_agents = min(int(data.get("n_agents", 100)), current_app.config.get("MAX_AGENTS", 1000))
    population = data.get("population", "European")
    seed = data.get("seed")

    try:
        personas = generate_synthetic_cohort(
            n_agents=n_agents,
            drug=drug,
            dose_mg=dose_mg,
            population=population,
            seed=seed,
        )

        cohort_id = str(uuid.uuid4())
        _cohorts[cohort_id] = {
            "id": cohort_id,
            "filename": f"synthetic_{population}_{n_agents}",
            "drug": drug,
            "dose_mg": dose_mg,
            "personas": personas,
            "sample_count": n_agents,
            "metadata": {"format": "synthetic", "population": population},
        }

        return jsonify({
            "cohort_id": cohort_id,
            "sample_count": n_agents,
            "drug": drug,
            "dose_mg": dose_mg,
            "population": population,
            "preview": personas[:3],
        }), 201

    except Exception as e:
        logger.error(f"Synthetic cohort error: {e}")
        return jsonify({"error": str(e)}), 500


@cohort_bp.route("/<cohort_id>", methods=["GET"])
def get_cohort(cohort_id: str):
    cohort = _cohorts.get(cohort_id)
    if not cohort:
        return jsonify({"error": "Cohort not found"}), 404
    # Return summary without full persona list for efficiency
    return jsonify({
        "id": cohort["id"],
        "filename": cohort["filename"],
        "drug": cohort["drug"],
        "dose_mg": cohort["dose_mg"],
        "sample_count": cohort["sample_count"],
        "metadata": cohort["metadata"],
    })


@cohort_bp.route("/<cohort_id>/personas", methods=["GET"])
def get_personas(cohort_id: str):
    cohort = _cohorts.get(cohort_id)
    if not cohort:
        return jsonify({"error": "Cohort not found"}), 404
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    return jsonify({
        "total": cohort["sample_count"],
        "personas": cohort["personas"][offset:offset + limit],
    })


def get_cohort_personas(cohort_id: str):
    """Internal helper used by simulation API."""
    cohort = _cohorts.get(cohort_id)
    if cohort:
        return cohort["personas"]
    return None
