"""GenomicSwarm Flask application factory."""

import os
import warnings
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, request
from flask_cors import CORS

from .config import Config
from .utils.logger import setup_logger, get_logger


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    if hasattr(app, "json") and hasattr(app.json, "ensure_ascii"):
        app.json.ensure_ascii = False

    logger = setup_logger("genomicswarm")

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Ensure upload dirs exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Validate config (non-fatal warnings)
    warnings_list = config_class.validate()
    for w in warnings_list:
        logger.warning(f"Config: {w}")

    @app.before_request
    def log_request():
        log = get_logger("genomicswarm.request")
        log.debug(f"{request.method} {request.path}")

    from .api import cohort_bp, simulation_bp, report_bp
    app.register_blueprint(cohort_bp, url_prefix="/api/cohort")
    app.register_blueprint(simulation_bp, url_prefix="/api/simulation")
    app.register_blueprint(report_bp, url_prefix="/api/report")

    @app.route("/health")
    def health():
        return {"status": "ok", "service": "GenomicSwarm Backend", "version": "1.0.0"}

    @app.route("/api/drugs")
    def list_drugs():
        from app.services.genomics.cpic_data import AVAILABLE_DRUGS, DRUG_GENE_PAIRS
        return {
            "drugs": [
                {
                    "name": drug,
                    "gene": info["primary_gene"],
                    "tier": info.get("cpic_tier", "B"),
                    "mechanism_short": info.get("mechanism", "")[:80],
                }
                for drug, info in DRUG_GENE_PAIRS.items()
            ]
        }

    @app.route("/api/populations")
    def list_populations():
        from app.services.genomics.cpic_data import POPULATION_ALLELE_FREQUENCIES
        return {"populations": list(POPULATION_ALLELE_FREQUENCIES.keys())}

    logger.info("GenomicSwarm backend ready.")
    return app
