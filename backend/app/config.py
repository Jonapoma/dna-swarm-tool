"""GenomicSwarm backend configuration."""

import os
from dotenv import load_dotenv

# Load .env from project root
_root_env = os.path.join(os.path.dirname(__file__), "../../.env")
if os.path.exists(_root_env):
    load_dotenv(_root_env, override=True)
else:
    load_dotenv(override=True)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "genomicswarm-dev-secret")
    DEBUG = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    JSON_AS_ASCII = False

    # Anthropic
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
    CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")

    # Upload
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "../uploads")
    ALLOWED_EXTENSIONS = {"vcf", "txt", "tsv", "gz"}

    # Simulation
    MAX_AGENTS = int(os.environ.get("MAX_AGENTS", "1000"))
    SIM_WORKERS = int(os.environ.get("SIM_WORKERS", "10"))

    @classmethod
    def validate(cls):
        errors = []
        if not cls.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY is not set — Claude API calls will use fallback mode")
        return errors
