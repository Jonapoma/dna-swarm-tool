"""
Persona Generator — converts a PGx profile into a MiroFish-compatible
agent seed persona (JSON) suitable for swarm simulation.
"""

from __future__ import annotations

import hashlib
import random
import uuid
from typing import Dict, List, Optional

from .pharmacogenomics import build_pgx_profile, predict_pk_pd, PHENOTYPE_CALLERS
from .cpic_data import POPULATION_ALLELE_FREQUENCIES, DRUG_GENE_PAIRS
from app.utils.logger import get_logger

logger = get_logger("genomicswarm.persona")

GenomeDict = Dict[str, str]


# ---------------------------------------------------------------------------
# Persona builder — single sample
# ---------------------------------------------------------------------------

def build_persona(
    genome: GenomeDict,
    sample_id: str,
    drug: str,
    dose_mg: float,
    demographics: Optional[dict] = None,
) -> dict:
    """
    Build a complete agent persona from genome data + drug configuration.

    Returns a dict ready to seed a swarm agent.
    """
    pgx_profile = build_pgx_profile(genome)
    pk_pd = predict_pk_pd(pgx_profile, drug, dose_mg)

    demo = demographics or {}
    age = demo.get("age", _random_age())
    sex = demo.get("sex", random.choice(["M", "F"]))
    weight_kg = demo.get("weight_kg", _random_weight(sex))
    population = demo.get("population", "European")

    # Derive clinical traits from PGx profile
    traits = _derive_clinical_traits(pgx_profile, pk_pd)

    # Construct human-readable phenotype summary
    phenotype_summary = _build_phenotype_summary(pgx_profile)

    persona = {
        # Identity
        "id": sample_id,
        "agent_id": f"agent_{hashlib.md5(sample_id.encode()).hexdigest()[:8]}",

        # Demographics
        "age": age,
        "sex": sex,
        "weight_kg": weight_kg,
        "population": population,

        # Pharmacogenomics
        "gene_phenotypes": pgx_profile["gene_phenotypes"],
        "phenotype_summary": phenotype_summary,
        "pgx_coverage": pgx_profile["coverage"],

        # Drug trial context
        "drug": drug,
        "dose_mg": dose_mg,
        "pk_pd": pk_pd,

        # Derived traits for simulation
        "traits": traits,

        # Simulation seed — natural language description for Claude
        "agent_description": _build_agent_description(
            sample_id, age, sex, pgx_profile, pk_pd, traits
        ),

        # Raw SNP count
        "snp_count": len(genome),
        "pgx_snp_count": len(pgx_profile["snp_results"]),
    }

    return persona


# ---------------------------------------------------------------------------
# Cohort builder
# ---------------------------------------------------------------------------

def build_cohort_personas(
    cohort_genomes: Dict[str, GenomeDict],
    drug: str,
    dose_mg: float,
    demographics_map: Optional[Dict[str, dict]] = None,
    max_agents: int = 1000,
) -> List[dict]:
    """
    Build personas for all samples in a cohort.
    """
    personas = []
    samples = list(cohort_genomes.items())[:max_agents]
    demo_map = demographics_map or {}

    for sample_id, genome in samples:
        try:
            persona = build_persona(
                genome=genome,
                sample_id=sample_id,
                drug=drug,
                dose_mg=dose_mg,
                demographics=demo_map.get(sample_id),
            )
            personas.append(persona)
        except Exception as e:
            logger.warning(f"Failed to build persona for {sample_id}: {e}")

    logger.info(f"Built {len(personas)} personas for cohort simulation of {drug}")
    return personas


# ---------------------------------------------------------------------------
# Synthetic cohort generator (for demo/testing)
# ---------------------------------------------------------------------------

def generate_synthetic_cohort(
    n_agents: int,
    drug: str,
    dose_mg: float,
    population: str = "European",
    seed: Optional[int] = None,
) -> List[dict]:
    """
    Generate a synthetic cohort using population allele frequencies.
    Useful for demo runs when no real DNA data is uploaded.
    """
    rng = random.Random(seed)
    freqs = POPULATION_ALLELE_FREQUENCIES.get(population, POPULATION_ALLELE_FREQUENCIES["European"])

    personas = []
    for i in range(n_agents):
        sample_id = f"synthetic_{population}_{i:04d}"

        # Assign phenotypes based on population frequencies
        gene_phenotypes = _sample_phenotypes_from_frequencies(freqs, rng)

        # Build a minimal PGx profile from sampled phenotypes
        pgx_profile = {
            "gene_phenotypes": gene_phenotypes,
            "snp_results": [],
            "coverage": {
                gene: {"phenotype": phen, "description": phen.replace("_", " ")}
                for gene, phen in gene_phenotypes.items()
            },
            "drug_relevance": {},
        }

        # Compute drug relevance from phenotypes
        for d, drug_info in DRUG_GENE_PAIRS.items():
            primary_gene = drug_info["primary_gene"]
            phen = gene_phenotypes.get(primary_gene, "normal_metabolizer")
            rec = drug_info["recommendations"].get(phen, {})
            if rec:
                pgx_profile["drug_relevance"][d] = {
                    "gene": primary_gene,
                    "phenotype": phen,
                    "action": rec.get("action"),
                    "efficacy_modifier": rec.get("efficacy_modifier", 1.0),
                    "toxicity_risk": rec.get("toxicity_risk", "standard"),
                }

        pk_pd = predict_pk_pd(pgx_profile, drug, dose_mg)
        traits = _derive_clinical_traits(pgx_profile, pk_pd)
        age = rng.randint(25, 75)
        sex = rng.choice(["M", "F"])
        weight_kg = _random_weight(sex, rng)

        persona = {
            "id": sample_id,
            "agent_id": f"agent_{i:04d}",
            "age": age,
            "sex": sex,
            "weight_kg": weight_kg,
            "population": population,
            "gene_phenotypes": gene_phenotypes,
            "phenotype_summary": _build_phenotype_summary(pgx_profile),
            "pgx_coverage": pgx_profile["coverage"],
            "drug": drug,
            "dose_mg": dose_mg,
            "pk_pd": pk_pd,
            "traits": traits,
            "agent_description": _build_agent_description(
                sample_id, age, sex, pgx_profile, pk_pd, traits
            ),
            "snp_count": 0,
            "pgx_snp_count": 0,
            "synthetic": True,
        }
        personas.append(persona)

    logger.info(f"Generated {n_agents} synthetic {population} agents for {drug} {dose_mg}mg trial")
    return personas


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _sample_phenotypes_from_frequencies(freqs: dict, rng: random.Random) -> dict:
    """Sample gene phenotypes from population frequency distributions."""
    phenotypes = {}

    gene_keys = {
        "CYP2D6": ["CYP2D6_poor_metabolizer", "CYP2D6_intermediate_metabolizer",
                   "CYP2D6_normal_metabolizer", "CYP2D6_ultrarapid_metabolizer"],
        "CYP2C19": ["CYP2C19_poor_metabolizer", "CYP2C19_intermediate_metabolizer",
                    "CYP2C19_normal_metabolizer", "CYP2C19_rapid_metabolizer",
                    "CYP2C19_ultrarapid_metabolizer"],
        "DPYD": ["DPYD_low_activity", "DPYD_intermediate_activity", "DPYD_normal_activity"],
        "TPMT": ["TPMT_low_activity", "TPMT_intermediate_activity", "TPMT_normal_activity"],
        "SLCO1B1": ["SLCO1B1_low_function", "SLCO1B1_intermediate_function", "SLCO1B1_normal_function"],
    }

    for gene, keys in gene_keys.items():
        probs = [freqs.get(k, 0.0) for k in keys]
        total = sum(probs)
        if total == 0:
            phenotypes[gene] = "normal_metabolizer"
            continue
        probs = [p / total for p in probs]

        r = rng.random()
        cumulative = 0.0
        selected = keys[-1]
        for key, prob in zip(keys, probs):
            cumulative += prob
            if r < cumulative:
                selected = key
                break

        # Strip gene prefix from key
        phenotypes[gene] = selected.replace(f"{gene}_", "")

    # Defaults for genes not in frequency table
    for gene in ["CYP2C9", "VKORC1", "CYP3A5"]:
        phenotypes[gene] = "normal_metabolizer" if gene != "VKORC1" else "moderate_sensitivity"

    return phenotypes


def _derive_clinical_traits(pgx_profile: dict, pk_pd: dict) -> List[str]:
    """Derive plain-language clinical trait tags from PGx profile."""
    traits = []
    phenotypes = pgx_profile["gene_phenotypes"]

    cyp2d6 = phenotypes.get("CYP2D6", "")
    if cyp2d6 == "poor_metabolizer":
        traits.append("CYP2D6_poor_metabolizer")
        traits.append("opioid_prodrug_non_responder")
    elif cyp2d6 == "ultrarapid_metabolizer":
        traits.append("CYP2D6_ultrarapid_metabolizer")
        traits.append("opioid_prodrug_toxicity_risk")
    elif cyp2d6 == "intermediate_metabolizer":
        traits.append("CYP2D6_intermediate_metabolizer")

    cyp2c19 = phenotypes.get("CYP2C19", "")
    if cyp2c19 == "poor_metabolizer":
        traits.append("CYP2C19_poor_metabolizer")
        traits.append("clopidogrel_non_responder")
    elif cyp2c19 in ("rapid_metabolizer", "ultrarapid_metabolizer"):
        traits.append(f"CYP2C19_{cyp2c19}")

    dpyd = phenotypes.get("DPYD", "")
    if dpyd == "low_activity":
        traits.append("DPYD_deficient")
        traits.append("5FU_contraindicated")
    elif dpyd == "intermediate_activity":
        traits.append("DPYD_intermediate")
        traits.append("5FU_dose_reduction_required")

    tpmt = phenotypes.get("TPMT", "")
    if tpmt == "low_activity":
        traits.append("TPMT_deficient")
        traits.append("thiopurine_myelosuppression_risk")
    elif tpmt == "intermediate_activity":
        traits.append("TPMT_intermediate")

    slco1b1 = phenotypes.get("SLCO1B1", "")
    if slco1b1 == "low_function":
        traits.append("SLCO1B1_reduced")
        traits.append("statin_myopathy_risk_high")
    elif slco1b1 == "intermediate_function":
        traits.append("statin_myopathy_risk_moderate")

    # Drug-specific trait
    rec = pk_pd.get("recommendation", "")
    if rec == "avoid":
        traits.append(f"{pk_pd['drug'].lower().replace(' ', '_')}_contraindicated")
    elif rec in ("reduce_dose_50pct", "reduce_dose_30_70pct", "use_lower_dose"):
        traits.append(f"{pk_pd['drug'].lower().replace(' ', '_')}_dose_reduction")
    elif rec == "standard_dosing":
        traits.append(f"{pk_pd['drug'].lower().replace(' ', '_')}_standard")

    return list(set(traits))


def _build_phenotype_summary(pgx_profile: dict) -> str:
    """One-sentence phenotype summary for display."""
    parts = []
    phenotypes = pgx_profile["gene_phenotypes"]

    for gene, phen in phenotypes.items():
        if "poor" in phen or "low" in phen or "deficient" in phen:
            parts.append(f"{gene}: {phen.replace('_', ' ')}")
        elif "ultrarapid" in phen:
            parts.append(f"{gene}: {phen.replace('_', ' ')}")

    if not parts:
        return "No clinically actionable PGx variants detected"
    return "; ".join(parts)


def _build_agent_description(
    sample_id: str,
    age: int,
    sex: str,
    pgx_profile: dict,
    pk_pd: dict,
    traits: List[str],
) -> str:
    """
    Build a natural-language agent description for Claude API simulation prompt.
    This is the persona seed text injected into the LLM context.
    """
    sex_word = "male" if sex == "M" else "female"
    phen_summary = _build_phenotype_summary(pgx_profile)

    drug = pk_pd["drug"]
    phenotype = pk_pd["phenotype"].replace("_", " ")
    rec = pk_pd["recommendation"].replace("_", " ")
    eff_mod = pk_pd["efficacy_modifier"]
    exposure = pk_pd.get("relative_exposure", 1.0)
    adrs = pk_pd.get("expected_adrs", [])
    adr_text = ", ".join(adrs[:4]) if adrs else "none predicted"

    return (
        f"Patient {sample_id}: {age}-year-old {sex_word}. "
        f"Pharmacogenomic profile: {phen_summary}. "
        f"For {drug}: {phenotype} (CPIC recommendation: {rec}). "
        f"Predicted drug exposure relative to normal: {exposure:.1f}x. "
        f"Efficacy modifier: {eff_mod:.2f}. "
        f"Expected adverse reactions: {adr_text}. "
        f"Clinical traits: {', '.join(traits[:6]) if traits else 'none'}."
    )


def _random_age(rng: random.Random = random) -> int:
    return rng.randint(25, 75)


def _random_weight(sex: str, rng: random.Random = random) -> float:
    if sex == "M":
        return round(rng.gauss(82, 12), 1)
    return round(rng.gauss(68, 11), 1)
