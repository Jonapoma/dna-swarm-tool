"""
PGx analysis engine — maps genome data to gene phenotypes.
Uses CPIC-aligned lookup tables from cpic_data.py.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .cpic_data import (
    SNP_DATABASE,
    PHENOTYPE_RULES,
    DRUG_GENE_PAIRS,
    ADR_PROFILES,
    COVERED_GENES,
)
from app.utils.logger import get_logger

logger = get_logger("genomicswarm.pgx")

GenomeDict = Dict[str, str]


# ---------------------------------------------------------------------------
# SNP-level analysis
# ---------------------------------------------------------------------------

def analyse_snp(rsid: str, genotype: str) -> Optional[dict]:
    """
    Given an rsID and normalised genotype, return the SNP interpretation.
    Returns None if SNP not in database.
    """
    snp_info = SNP_DATABASE.get(rsid)
    if not snp_info:
        return None

    effects = snp_info.get("genotype_effects", {})
    if genotype in effects:
        effect_level, description = effects[genotype]
    else:
        effect_level, description = "unknown", "Genotype not in reference table"

    return {
        "rsid": rsid,
        "gene": snp_info["gene"],
        "allele": snp_info["allele"],
        "genotype": genotype,
        "effect_level": effect_level,
        "description": description,
        "snp_effect": snp_info["effect"],
    }


# ---------------------------------------------------------------------------
# Gene phenotype calling
# ---------------------------------------------------------------------------

def call_cyp2d6_phenotype(genome: GenomeDict) -> str:
    """
    Determine CYP2D6 metabolizer phenotype from tag SNPs.
    This is a simplified star-allele approximation.
    CYP2D6 CNV (duplications) is not detectable from SNP arrays.
    """
    lof_count = 0  # loss-of-function alleles

    # rs3892097: *4 allele (A = LOF)
    gt = genome.get("rs3892097")
    if gt:
        lof_count += gt.count("A")

    # rs35742686: *3 allele (T = LOF)
    gt = genome.get("rs35742686")
    if gt:
        lof_count += gt.count("T")

    # rs5030655: *6 allele (A = LOF)
    gt = genome.get("rs5030655")
    if gt:
        lof_count += gt.count("A")

    if lof_count >= 2:
        return "poor_metabolizer"
    elif lof_count == 1:
        return "intermediate_metabolizer"

    # Check for gain-of-function indicator (rs16947 homozygous A → UM proxy)
    gt = genome.get("rs16947")
    if gt == "AA":
        return "ultrarapid_metabolizer"

    return "normal_metabolizer"


def call_cyp2c19_phenotype(genome: GenomeDict) -> str:
    """Determine CYP2C19 phenotype from *2, *3, *17 tag SNPs."""
    lof_count = 0
    gain_count = 0

    # *2 allele (rs4244285 A = LOF)
    gt = genome.get("rs4244285")
    if gt:
        lof_count += gt.count("A")

    # *3 allele (rs4986893 A = LOF)
    gt = genome.get("rs4986893")
    if gt:
        lof_count += gt.count("A")

    # *17 allele (rs12248560 T = gain-of-function)
    gt = genome.get("rs12248560")
    if gt:
        gain_count += gt.count("T")

    if lof_count >= 2:
        return "poor_metabolizer"
    elif lof_count == 1:
        return "intermediate_metabolizer"
    elif gain_count >= 2:
        return "ultrarapid_metabolizer"
    elif gain_count == 1:
        return "rapid_metabolizer"
    return "normal_metabolizer"


def call_cyp2c9_phenotype(genome: GenomeDict) -> str:
    """Determine CYP2C9 phenotype from *2 and *3 tag SNPs."""
    # *2 (rs1799853 T = reduced)
    # *3 (rs1057910 C = LOF)
    star2_count = 0
    star3_count = 0

    gt = genome.get("rs1799853")
    if gt:
        star2_count += gt.count("T")

    gt = genome.get("rs1057910")
    if gt:
        star3_count += gt.count("C")

    if star3_count >= 1 or (star2_count + star3_count) >= 2:
        return "poor_metabolizer"
    elif star2_count == 1 or star3_count == 1:
        return "intermediate_metabolizer"
    return "normal_metabolizer"


def call_vkorc1_phenotype(genome: GenomeDict) -> str:
    """Determine VKORC1 warfarin sensitivity."""
    gt = genome.get("rs9923231") or genome.get("rs9934438")
    if not gt:
        return "unknown"
    if gt == "TT":
        return "high_sensitivity"
    elif gt == "CT":
        return "moderate_sensitivity"
    return "low_sensitivity"


def call_dpyd_phenotype(genome: GenomeDict) -> str:
    """Determine DPYD (DPD) activity status."""
    lof_alleles = 0

    # *2A (rs3918290 A = LOF)
    gt = genome.get("rs3918290")
    if gt:
        lof_alleles += gt.count("A")

    # c.1679T>G (rs55886062 C = LOF)
    gt = genome.get("rs55886062")
    if gt:
        lof_alleles += gt.count("C")

    # c.2846A>T (rs67376798 T = reduced)
    gt = genome.get("rs67376798")
    if gt:
        lof_alleles += gt.count("T")

    if lof_alleles >= 2:
        return "low_activity"
    elif lof_alleles == 1:
        return "intermediate_activity"
    return "normal_activity"


def call_tpmt_phenotype(genome: GenomeDict) -> str:
    """Determine TPMT activity status."""
    lof_alleles = 0

    # *2 (rs1800462 T = LOF)
    gt = genome.get("rs1800462")
    if gt:
        lof_alleles += gt.count("T")

    # *3B (rs1800460 T = LOF)
    gt = genome.get("rs1800460")
    if gt:
        lof_alleles += gt.count("T")

    # *3C (rs1142345 C = LOF)
    gt = genome.get("rs1142345")
    if gt:
        lof_alleles += gt.count("C")

    if lof_alleles >= 2:
        return "low_activity"
    elif lof_alleles == 1:
        return "intermediate_activity"
    return "normal_activity"


def call_slco1b1_phenotype(genome: GenomeDict) -> str:
    """Determine SLCO1B1 transporter function (statin myopathy)."""
    gt = genome.get("rs4149056")
    if not gt:
        return "normal_function"
    if gt == "CC":
        return "low_function"
    elif gt == "TC":
        return "intermediate_function"
    return "normal_function"


def call_cyp3a5_phenotype(genome: GenomeDict) -> str:
    """Determine CYP3A5 expression status (tacrolimus)."""
    gt = genome.get("rs776746")
    if not gt:
        return "non_expressor"  # Most common in Europeans
    if gt == "AA":
        return "expressor"
    elif gt == "AG":
        return "low_expressor"
    return "non_expressor"


PHENOTYPE_CALLERS = {
    "CYP2D6": call_cyp2d6_phenotype,
    "CYP2C19": call_cyp2c19_phenotype,
    "CYP2C9": call_cyp2c9_phenotype,
    "VKORC1": call_vkorc1_phenotype,
    "DPYD": call_dpyd_phenotype,
    "TPMT": call_tpmt_phenotype,
    "SLCO1B1": call_slco1b1_phenotype,
    "CYP3A5": call_cyp3a5_phenotype,
}


# ---------------------------------------------------------------------------
# Full genome → phenotype profile
# ---------------------------------------------------------------------------

def build_pgx_profile(genome: GenomeDict) -> dict:
    """
    Run all phenotype callers against a genome dict.
    Returns a complete PGx profile.
    """
    profile: dict = {
        "gene_phenotypes": {},
        "snp_results": [],
        "coverage": {},
        "drug_relevance": {},
    }

    # Call phenotypes for all covered genes
    for gene, caller in PHENOTYPE_CALLERS.items():
        phenotype = caller(genome)
        profile["gene_phenotypes"][gene] = phenotype

        # Attach phenotype description
        if gene in PHENOTYPE_RULES and phenotype in PHENOTYPE_RULES[gene]:
            rule = PHENOTYPE_RULES[gene][phenotype]
            profile["coverage"][gene] = {
                "phenotype": phenotype,
                "description": rule["description"],
                "prevalence_european": rule.get("prevalence_european"),
            }
        else:
            profile["coverage"][gene] = {"phenotype": phenotype, "description": phenotype}

    # Analyse individual SNPs
    for rsid, genotype in genome.items():
        result = analyse_snp(rsid, genotype)
        if result:
            profile["snp_results"].append(result)

    # Map phenotypes to relevant drugs
    for drug, drug_info in DRUG_GENE_PAIRS.items():
        primary_gene = drug_info["primary_gene"]
        phenotype = profile["gene_phenotypes"].get(primary_gene, "unknown")
        recommendation = drug_info["recommendations"].get(phenotype)

        if recommendation:
            profile["drug_relevance"][drug] = {
                "gene": primary_gene,
                "phenotype": phenotype,
                "action": recommendation.get("action"),
                "reason": recommendation.get("reason", ""),
                "efficacy_modifier": recommendation.get("efficacy_modifier", 1.0),
                "toxicity_risk": recommendation.get("toxicity_risk", "unknown"),
                "alternative": recommendation.get("alternative"),
                "cpic_tier": drug_info.get("cpic_tier", "B"),
            }

    return profile


# ---------------------------------------------------------------------------
# Drug-specific PK/PD predictor
# ---------------------------------------------------------------------------

def predict_pk_pd(pgx_profile: dict, drug: str, dose_mg: float) -> dict:
    """
    Predict pharmacokinetic/pharmacodynamic outcomes for a given drug + dose.
    Returns structured PK/PD parameters.
    """
    drug_lower = drug.lower().replace("-", "")
    # Normalise common names
    name_map = {
        "5fluorouracil": "5-fluorouracil",
        "5fu": "5-fluorouracil",
        "capecitabine": "capecitabine",
        "azathioprine": "azathioprine",
        "6mp": "azathioprine",
    }
    drug_key = name_map.get(drug_lower, drug_lower)

    drug_info = DRUG_GENE_PAIRS.get(drug_key)
    if not drug_info:
        return {
            "drug": drug,
            "dose_mg": dose_mg,
            "gene": "unknown",
            "phenotype": "unknown",
            "efficacy_modifier": 1.0,
            "predicted_exposure": "unknown",
            "toxicity_risk": "unknown",
            "recommendation": "no_data",
            "note": f"Drug '{drug}' not in CPIC database. Simulation uses population-average response.",
        }

    primary_gene = drug_info["primary_gene"]
    phenotype = pgx_profile["gene_phenotypes"].get(primary_gene, "unknown")
    recommendation = drug_info["recommendations"].get(phenotype, {})
    efficacy_mod = recommendation.get("efficacy_modifier", 1.0)

    # Compute expected relative exposure vs. normal metabolizer
    exposure_map = {
        "ultrarapid_metabolizer": 0.4,
        "rapid_metabolizer": 0.7,
        "normal_metabolizer": 1.0,
        "intermediate_metabolizer": 1.6,
        "poor_metabolizer": 3.0,
        "expressor": 0.5,
        "low_expressor": 0.75,
        "non_expressor": 1.0,
        "normal_function": 1.0,
        "intermediate_function": 1.5,
        "low_function": 2.5,
        "normal_activity": 1.0,
        "intermediate_activity": 2.0,
        "low_activity": 5.0,
        "high_sensitivity": 2.0,
        "moderate_sensitivity": 1.3,
        "low_sensitivity": 0.7,
        "unknown": 1.0,
    }
    relative_exposure = exposure_map.get(phenotype, 1.0)

    adr_list = ADR_PROFILES.get(drug_key, {}).get(phenotype) or \
               ADR_PROFILES.get(drug_key, {}).get("normal_metabolizer") or []

    return {
        "drug": drug,
        "dose_mg": dose_mg,
        "gene": primary_gene,
        "phenotype": phenotype,
        "phenotype_description": pgx_profile["coverage"].get(primary_gene, {}).get("description", ""),
        "efficacy_modifier": efficacy_mod,
        "relative_exposure": relative_exposure,
        "adjusted_effective_dose_mg": round(dose_mg * efficacy_mod, 2),
        "predicted_auc_ratio": relative_exposure,
        "toxicity_risk": recommendation.get("toxicity_risk", "standard"),
        "recommendation": recommendation.get("action", "standard_dosing"),
        "recommendation_reason": recommendation.get("reason", ""),
        "alternative_drug": recommendation.get("alternative"),
        "expected_adrs": adr_list,
        "mechanism": drug_info.get("mechanism", ""),
    }
