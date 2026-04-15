"""
CPIC-aligned pharmacogenomics knowledge base.
Sources: CPIC guidelines (cpicpgx.org), PharmGKB, FDA Table of Pharmacogenomic Biomarkers.
Covers Tier A (highest evidence) and select Tier B drug-gene pairs.
"""

# ---------------------------------------------------------------------------
# SNP DATABASE — rsID → gene/allele metadata
# ---------------------------------------------------------------------------

SNP_DATABASE = {
    # ── CYP2D6 ────────────────────────────────────────────────────────────
    "rs3892097": {
        "gene": "CYP2D6", "allele": "CYP2D6*4",
        "effect": "loss_of_function",
        "description": "Most common loss-of-function allele in Europeans (~21%)",
        "risk_allele": "A",
        "ref_allele": "G",
        "genotype_effects": {
            "GG": ("normal_function", "CYP2D6*1/*1 — two functional alleles"),
            "AG": ("reduced_function", "CYP2D6*1/*4 — one functional, one non-functional"),
            "AA": ("no_function", "CYP2D6*4/*4 — poor metabolizer (homozygous LOF)"),
        }
    },
    "rs35742686": {
        "gene": "CYP2D6", "allele": "CYP2D6*3",
        "effect": "loss_of_function",
        "description": "Frame-shift deletion; loss-of-function allele (~1-2%)",
        "risk_allele": "T",
        "ref_allele": "C",
        "genotype_effects": {
            "CC": ("normal_function", "No *3 allele present"),
            "CT": ("reduced_function", "Heterozygous CYP2D6*3 carrier"),
            "TT": ("no_function", "Homozygous CYP2D6*3 — rare"),
        }
    },
    "rs5030655": {
        "gene": "CYP2D6", "allele": "CYP2D6*6",
        "effect": "loss_of_function",
        "description": "1-bp deletion causing frame-shift (~1%)",
        "risk_allele": "A",
        "ref_allele": "G",
        "genotype_effects": {
            "GG": ("normal_function", "No *6 allele"),
            "AG": ("reduced_function", "Heterozygous CYP2D6*6"),
            "AA": ("no_function", "Homozygous CYP2D6*6 — rare"),
        }
    },
    "rs16947": {
        "gene": "CYP2D6", "allele": "CYP2D6*2",
        "effect": "normal_function",
        "description": "CYP2D6*2 allele — normal or slightly increased activity",
        "risk_allele": "A",
        "ref_allele": "G",
        "genotype_effects": {
            "GG": ("normal_function", "CYP2D6*1 background"),
            "AG": ("normal_function", "Heterozygous *2"),
            "AA": ("increased_function", "Homozygous *2 — may contribute to UM phenotype"),
        }
    },

    # ── CYP2C19 ───────────────────────────────────────────────────────────
    "rs4244285": {
        "gene": "CYP2C19", "allele": "CYP2C19*2",
        "effect": "loss_of_function",
        "description": "Most common LOF allele (~15% Europeans, ~30% East Asians)",
        "risk_allele": "A",
        "ref_allele": "G",
        "genotype_effects": {
            "GG": ("normal_function", "No *2 allele — normal metabolizer baseline"),
            "AG": ("reduced_function", "CYP2C19*1/*2 — intermediate metabolizer"),
            "AA": ("no_function", "CYP2C19*2/*2 — poor metabolizer"),
        }
    },
    "rs4986893": {
        "gene": "CYP2C19", "allele": "CYP2C19*3",
        "effect": "loss_of_function",
        "description": "Loss-of-function allele, mainly East Asians (~5%)",
        "risk_allele": "A",
        "ref_allele": "G",
        "genotype_effects": {
            "GG": ("normal_function", "No *3 allele"),
            "AG": ("reduced_function", "CYP2C19*1/*3 — intermediate metabolizer"),
            "AA": ("no_function", "CYP2C19*3/*3 — poor metabolizer (rare)"),
        }
    },
    "rs12248560": {
        "gene": "CYP2C19", "allele": "CYP2C19*17",
        "effect": "increased_function",
        "description": "Gain-of-function allele — ultrarapid metabolizer (~20% Europeans)",
        "risk_allele": "T",
        "ref_allele": "C",
        "genotype_effects": {
            "CC": ("normal_function", "No *17 allele"),
            "CT": ("increased_function", "CYP2C19*1/*17 — rapid metabolizer"),
            "TT": ("ultrarapid_function", "CYP2C19*17/*17 — ultrarapid metabolizer"),
        }
    },

    # ── CYP2C9 (warfarin dosing) ──────────────────────────────────────────
    "rs1799853": {
        "gene": "CYP2C9", "allele": "CYP2C9*2",
        "effect": "reduced_function",
        "description": "Arg144Cys — moderately reduced activity (~11% Europeans)",
        "risk_allele": "T",
        "ref_allele": "C",
        "genotype_effects": {
            "CC": ("normal_function", "CYP2C9*1 — normal warfarin clearance"),
            "CT": ("reduced_function", "CYP2C9*1/*2 — ~30% reduced clearance"),
            "TT": ("significantly_reduced", "CYP2C9*2/*2 — ~50% reduced clearance"),
        }
    },
    "rs1057910": {
        "gene": "CYP2C9", "allele": "CYP2C9*3",
        "effect": "loss_of_function",
        "description": "Ile359Leu — severely reduced activity (~7% Europeans)",
        "risk_allele": "C",
        "ref_allele": "A",
        "genotype_effects": {
            "AA": ("normal_function", "CYP2C9*1 — normal"),
            "AC": ("significantly_reduced", "CYP2C9*1/*3 — ~80% reduced clearance"),
            "CC": ("near_absent", "CYP2C9*3/*3 — ~95% reduced clearance"),
        }
    },

    # ── VKORC1 (warfarin sensitivity) ─────────────────────────────────────
    "rs9923231": {
        "gene": "VKORC1", "allele": "VKORC1 -1639G>A",
        "effect": "warfarin_sensitivity",
        "description": "Promoter variant reducing VKORC1 expression → warfarin sensitivity",
        "risk_allele": "T",
        "ref_allele": "C",
        "genotype_effects": {
            "CC": ("low_sensitivity", "GG genotype — high warfarin dose typically needed (~45mg/wk)"),
            "CT": ("moderate_sensitivity", "GA genotype — intermediate dose (~35mg/wk)"),
            "TT": ("high_sensitivity", "AA genotype — low warfarin dose needed (~25mg/wk)"),
        }
    },
    "rs9934438": {
        "gene": "VKORC1", "allele": "VKORC1 1173C>T",
        "effect": "warfarin_sensitivity",
        "description": "Intron variant in strong LD with -1639G>A",
        "risk_allele": "T",
        "ref_allele": "C",
        "genotype_effects": {
            "CC": ("low_sensitivity", "Low warfarin sensitivity"),
            "CT": ("moderate_sensitivity", "Moderate sensitivity"),
            "TT": ("high_sensitivity", "High warfarin sensitivity — lower dose required"),
        }
    },

    # ── SLCO1B1 (statin myopathy) ─────────────────────────────────────────
    "rs4149056": {
        "gene": "SLCO1B1", "allele": "SLCO1B1*5",
        "effect": "reduced_transport",
        "description": "Val174Ala — reduced hepatic statin uptake → elevated plasma levels → myopathy",
        "risk_allele": "C",
        "ref_allele": "T",
        "genotype_effects": {
            "TT": ("normal_function", "Normal statin transport — standard dosing"),
            "TC": ("reduced_function", "Heterozygous *5 — moderate myopathy risk (~4.5x)"),
            "CC": ("significantly_reduced", "Homozygous *5 — high myopathy risk (~16.9x)"),
        }
    },

    # ── DPYD (5-FU / capecitabine toxicity) ──────────────────────────────
    "rs3918290": {
        "gene": "DPYD", "allele": "DPYD*2A",
        "effect": "loss_of_function",
        "description": "IVS14+1G>A splice site — severe 5-FU toxicity risk (~1% Europeans)",
        "risk_allele": "A",
        "ref_allele": "G",
        "genotype_effects": {
            "GG": ("normal_function", "Normal DPD activity — standard 5-FU dosing"),
            "AG": ("reduced_function", "Heterozygous DPYD*2A — 50% dose reduction recommended"),
            "AA": ("absent_function", "Homozygous DPYD*2A — 5-FU contraindicated (fatal toxicity risk)"),
        }
    },
    "rs55886062": {
        "gene": "DPYD", "allele": "DPYD c.1679T>G",
        "effect": "loss_of_function",
        "description": "I560S — major loss-of-function; high toxicity risk",
        "risk_allele": "C",
        "ref_allele": "A",
        "genotype_effects": {
            "AA": ("normal_function", "No DPYD c.1679T>G variant"),
            "AC": ("reduced_function", "Heterozygous — significant toxicity risk, dose reduction needed"),
            "CC": ("absent_function", "Homozygous — 5-FU contraindicated"),
        }
    },
    "rs67376798": {
        "gene": "DPYD", "allele": "DPYD c.2846A>T",
        "effect": "reduced_function",
        "description": "D949V — moderately reduced DPD activity",
        "risk_allele": "T",
        "ref_allele": "A",
        "genotype_effects": {
            "AA": ("normal_function", "Normal DPD"),
            "AT": ("reduced_function", "Heterozygous c.2846A>T — 25-50% dose reduction"),
            "TT": ("significantly_reduced", "Homozygous — avoid 5-FU or major dose reduction"),
        }
    },

    # ── TPMT (thiopurines: azathioprine, 6-MP, thioguanine) ──────────────
    "rs1800462": {
        "gene": "TPMT", "allele": "TPMT*2",
        "effect": "loss_of_function",
        "description": "Ala80Pro — loss-of-function (~0.4% Europeans)",
        "risk_allele": "T",
        "ref_allele": "C",
        "genotype_effects": {
            "CC": ("normal_function", "No *2 allele"),
            "CT": ("reduced_function", "Heterozygous TPMT*2 — intermediate activity"),
            "TT": ("absent_function", "Homozygous *2 — rare, very low TPMT activity"),
        }
    },
    "rs1800460": {
        "gene": "TPMT", "allele": "TPMT*3B",
        "effect": "loss_of_function",
        "description": "Ala154Thr — part of TPMT*3A haplotype (~3-5% Europeans)",
        "risk_allele": "T",
        "ref_allele": "C",
        "genotype_effects": {
            "CC": ("normal_function", "No *3B allele"),
            "CT": ("reduced_function", "Heterozygous *3B — intermediate TPMT activity"),
            "TT": ("absent_function", "Homozygous *3B — rare"),
        }
    },
    "rs1142345": {
        "gene": "TPMT", "allele": "TPMT*3C",
        "effect": "loss_of_function",
        "description": "Tyr240Cys — most common LOF variant in Europeans (~4.5%)",
        "risk_allele": "C",
        "ref_allele": "T",
        "genotype_effects": {
            "TT": ("normal_function", "Normal TPMT activity"),
            "TC": ("reduced_function", "Heterozygous *3C — intermediate activity, dose adjustment"),
            "CC": ("absent_function", "Homozygous *3C — thiopurines contraindicated at standard dose"),
        }
    },

    # ── CYP3A5 (tacrolimus dosing) ────────────────────────────────────────
    "rs776746": {
        "gene": "CYP3A5", "allele": "CYP3A5*3",
        "effect": "non_expressor",
        "description": "Splice defect — most Europeans are non-expressors (~85%)",
        "risk_allele": "G",
        "ref_allele": "A",
        "genotype_effects": {
            "AA": ("expressor", "CYP3A5*1/*1 — high tacrolimus clearance, higher dose needed"),
            "AG": ("low_expressor", "CYP3A5*1/*3 — intermediate clearance"),
            "GG": ("non_expressor", "CYP3A5*3/*3 — low clearance, standard tacrolimus dose"),
        }
    },

    # ── UGT1A1 (irinotecan, atazanavir) ──────────────────────────────────
    "rs8175347": {
        "gene": "UGT1A1", "allele": "UGT1A1*28",
        "effect": "reduced_function",
        "description": "TA-repeat promoter variant — reduced UGT1A1 expression (~35% Europeans)",
        "risk_allele": "7_repeat",
        "ref_allele": "6_repeat",
        "genotype_effects": {
            "6/6": ("normal_function", "Normal UGT1A1 expression — standard irinotecan"),
            "6/7": ("reduced_function", "Heterozygous *28 — moderate toxicity risk"),
            "7/7": ("significantly_reduced", "Homozygous *28 — high irinotecan toxicity (severe neutropenia)"),
        }
    },

    # ── MTHFR (methotrexate, folate) ──────────────────────────────────────
    "rs1801133": {
        "gene": "MTHFR", "allele": "MTHFR C677T",
        "effect": "reduced_function",
        "description": "Ala222Val — thermolabile variant, ~40-45% reduced enzyme activity",
        "risk_allele": "A",
        "ref_allele": "G",
        "genotype_effects": {
            "GG": ("normal_function", "Normal MTHFR activity"),
            "AG": ("reduced_function", "Heterozygous C677T — ~35% reduced activity"),
            "AA": ("significantly_reduced", "Homozygous C677T — ~70% reduced activity; methotrexate toxicity risk"),
        }
    },
    "rs1801131": {
        "gene": "MTHFR", "allele": "MTHFR A1298C",
        "effect": "reduced_function",
        "description": "Glu429Ala — milder effect than C677T, compound heterozygosity increases risk",
        "risk_allele": "C",
        "ref_allele": "T",
        "genotype_effects": {
            "TT": ("normal_function", "Normal MTHFR A1298"),
            "TC": ("mildly_reduced", "Heterozygous A1298C"),
            "CC": ("reduced_function", "Homozygous A1298C — compound risk if also C677T carrier"),
        }
    },

    # ── CYP1A2 (clozapine, caffeine) ──────────────────────────────────────
    "rs762551": {
        "gene": "CYP1A2", "allele": "CYP1A2*1F",
        "effect": "inducible",
        "description": "Promoter variant affecting inducibility by smoking (~50% of population)",
        "risk_allele": "A",
        "ref_allele": "C",
        "genotype_effects": {
            "CC": ("poor_inducer", "Lower CYP1A2 inducibility — clozapine may accumulate in smokers"),
            "CA": ("moderate_inducer", "Heterozygous *1F"),
            "AA": ("rapid_inducer", "High CYP1A2 inducibility — smokers may need higher clozapine dose"),
        }
    },
}

# ---------------------------------------------------------------------------
# PHENOTYPE DEFINITIONS — gene → diplotype patterns → phenotype
# ---------------------------------------------------------------------------

PHENOTYPE_RULES = {
    "CYP2D6": {
        "poor_metabolizer": {
            "description": "Two non-functional alleles. Prodrugs (codeine→morphine) not activated; parent compounds accumulate.",
            "prevalence_european": 0.07,
            "prevalence_asian": 0.01,
        },
        "intermediate_metabolizer": {
            "description": "One non-functional + one functional allele, or two reduced-function alleles.",
            "prevalence_european": 0.10,
            "prevalence_asian": 0.50,
        },
        "normal_metabolizer": {
            "description": "Two functional alleles. Standard drug response expected.",
            "prevalence_european": 0.70,
            "prevalence_asian": 0.45,
        },
        "ultrarapid_metabolizer": {
            "description": "Gene duplication or gain-of-function alleles. Prodrugs over-activated; may cause toxicity.",
            "prevalence_european": 0.05,
            "prevalence_asian": 0.01,
        },
    },
    "CYP2C19": {
        "poor_metabolizer": {
            "description": "Two LOF alleles. Clopidogrel cannot be activated; PPIs over-concentrated.",
            "prevalence_european": 0.02,
            "prevalence_asian": 0.15,
        },
        "intermediate_metabolizer": {
            "description": "One LOF + one functional allele.",
            "prevalence_european": 0.26,
            "prevalence_asian": 0.40,
        },
        "normal_metabolizer": {
            "description": "Two functional alleles (*1/*1 or *1/*17).",
            "prevalence_european": 0.50,
            "prevalence_asian": 0.42,
        },
        "rapid_metabolizer": {
            "description": "One *17 gain-of-function allele.",
            "prevalence_european": 0.18,
            "prevalence_asian": 0.03,
        },
        "ultrarapid_metabolizer": {
            "description": "Two *17 alleles. Very fast metabolism; drugs may be ineffective at standard doses.",
            "prevalence_european": 0.04,
            "prevalence_asian": 0.001,
        },
    },
    "CYP2C9": {
        "normal_metabolizer": {"description": "Normal warfarin clearance.", "prevalence_european": 0.65},
        "intermediate_metabolizer": {"description": "~30-60% reduced warfarin clearance.", "prevalence_european": 0.28},
        "poor_metabolizer": {"description": "Severely reduced warfarin clearance; bleeding risk.", "prevalence_european": 0.07},
    },
    "DPYD": {
        "normal_activity": {"description": "Full DPD enzyme — standard 5-FU dosing safe.", "prevalence_european": 0.96},
        "intermediate_activity": {"description": "~50% DPD activity — 25-50% dose reduction recommended.", "prevalence_european": 0.035},
        "low_activity": {"description": "Near-absent DPD — 5-FU/capecitabine contraindicated.", "prevalence_european": 0.005},
    },
    "TPMT": {
        "normal_activity": {"description": "High TPMT — standard thiopurine dose.", "prevalence_european": 0.89},
        "intermediate_activity": {"description": "Intermediate TPMT — reduce dose by 30-70%.", "prevalence_european": 0.10},
        "low_activity": {"description": "Low/absent TPMT — thiopurines at standard dose contraindicated.", "prevalence_european": 0.01},
    },
    "SLCO1B1": {
        "normal_function": {"description": "Normal hepatic statin uptake.", "prevalence_european": 0.72},
        "intermediate_function": {"description": "Moderately elevated statin plasma levels — monitor.", "prevalence_european": 0.24},
        "low_function": {"description": "High statin plasma levels — significant myopathy risk.", "prevalence_european": 0.04},
    },
}

# ---------------------------------------------------------------------------
# CPIC DRUG-GENE PAIRS — clinical recommendations
# ---------------------------------------------------------------------------

DRUG_GENE_PAIRS = {
    "codeine": {
        "primary_gene": "CYP2D6",
        "cpic_tier": "A",
        "mechanism": "CYP2D6 converts codeine (prodrug) to morphine (active). Poor metabolizers get no effect; ultrarapid metabolizers get dangerous morphine levels.",
        "recommendations": {
            "poor_metabolizer": {
                "action": "avoid",
                "reason": "Codeine not converted to morphine — inadequate analgesia. Risk of ineffective treatment.",
                "alternative": "Use non-opioid analgesics or opioids not dependent on CYP2D6 (e.g., morphine, hydromorphone).",
                "efficacy_modifier": 0.05,
                "toxicity_risk": "low_morphine_but_codeine_accumulation",
            },
            "intermediate_metabolizer": {
                "action": "use_with_caution",
                "reason": "Reduced conversion to morphine — reduced analgesia.",
                "alternative": "Consider alternative analgesic.",
                "efficacy_modifier": 0.55,
                "toxicity_risk": "low",
            },
            "normal_metabolizer": {
                "action": "standard_dosing",
                "reason": "Normal codeine-to-morphine conversion.",
                "alternative": None,
                "efficacy_modifier": 1.0,
                "toxicity_risk": "standard",
            },
            "ultrarapid_metabolizer": {
                "action": "avoid",
                "reason": "Excessive morphine production — risk of respiratory depression, especially in neonates/nursing infants.",
                "alternative": "Use non-opioid or non-CYP2D6 opioid.",
                "efficacy_modifier": 1.3,
                "toxicity_risk": "high_morphine_toxicity",
            },
        }
    },
    "tramadol": {
        "primary_gene": "CYP2D6",
        "cpic_tier": "A",
        "mechanism": "CYP2D6 activates tramadol to O-desmethyltramadol (M1), the active opioid metabolite.",
        "recommendations": {
            "poor_metabolizer": {
                "action": "avoid",
                "reason": "No active M1 metabolite — analgesia from opioid component absent; serotonergic effects still present.",
                "alternative": "Alternative analgesic (non-CYP2D6 opioid).",
                "efficacy_modifier": 0.1,
                "toxicity_risk": "serotonin_syndrome_risk",
            },
            "intermediate_metabolizer": {
                "action": "use_with_caution",
                "reason": "Reduced M1 production.",
                "alternative": None,
                "efficacy_modifier": 0.6,
                "toxicity_risk": "low",
            },
            "normal_metabolizer": {
                "action": "standard_dosing",
                "reason": "Normal M1 production.",
                "alternative": None,
                "efficacy_modifier": 1.0,
                "toxicity_risk": "standard",
            },
            "ultrarapid_metabolizer": {
                "action": "avoid",
                "reason": "Excessive M1 levels — opioid toxicity risk.",
                "alternative": "Non-CYP2D6 opioid analgesic.",
                "efficacy_modifier": 1.4,
                "toxicity_risk": "opioid_toxicity",
            },
        }
    },
    "clopidogrel": {
        "primary_gene": "CYP2C19",
        "cpic_tier": "A",
        "mechanism": "CYP2C19 converts clopidogrel (prodrug) to active thiol metabolite. Poor metabolizers cannot activate the drug → no antiplatelet effect → increased MACE risk.",
        "recommendations": {
            "poor_metabolizer": {
                "action": "avoid",
                "reason": "Minimal drug activation — significantly increased risk of major adverse cardiac events (MACE). FDA Black Box Warning.",
                "alternative": "Prasugrel or ticagrelor (not CYP2C19-dependent).",
                "efficacy_modifier": 0.05,
                "toxicity_risk": "therapeutic_failure_high",
            },
            "intermediate_metabolizer": {
                "action": "consider_alternative",
                "reason": "Reduced platelet inhibition — moderately elevated MACE risk.",
                "alternative": "Consider prasugrel/ticagrelor for ACS patients.",
                "efficacy_modifier": 0.55,
                "toxicity_risk": "moderate_therapeutic_failure",
            },
            "normal_metabolizer": {
                "action": "standard_dosing",
                "reason": "Standard clopidogrel response expected.",
                "alternative": None,
                "efficacy_modifier": 1.0,
                "toxicity_risk": "standard",
            },
            "rapid_metabolizer": {
                "action": "standard_dosing",
                "reason": "Potentially enhanced antiplatelet effect — standard dosing appropriate.",
                "alternative": None,
                "efficacy_modifier": 1.1,
                "toxicity_risk": "slightly_elevated_bleeding",
            },
            "ultrarapid_metabolizer": {
                "action": "standard_dosing",
                "reason": "Enhanced activation — possible increased bleeding risk.",
                "alternative": None,
                "efficacy_modifier": 1.15,
                "toxicity_risk": "elevated_bleeding_risk",
            },
        }
    },
    "warfarin": {
        "primary_gene": "CYP2C9",
        "secondary_genes": ["VKORC1"],
        "cpic_tier": "A",
        "mechanism": "CYP2C9 metabolizes S-warfarin. VKORC1 is the drug target. Variants in both genes alter optimal dose by 40-60%.",
        "dose_algorithm": "IWPC",
        "recommendations": {
            "CYP2C9_normal+VKORC1_low_sensitivity": {
                "weekly_dose_mg": 45, "action": "standard_dosing", "efficacy_modifier": 1.0,
            },
            "CYP2C9_normal+VKORC1_moderate_sensitivity": {
                "weekly_dose_mg": 35, "action": "standard_dosing", "efficacy_modifier": 1.0,
            },
            "CYP2C9_normal+VKORC1_high_sensitivity": {
                "weekly_dose_mg": 28, "action": "dose_reduction", "efficacy_modifier": 1.0,
            },
            "CYP2C9_intermediate+VKORC1_low_sensitivity": {
                "weekly_dose_mg": 33, "action": "dose_reduction", "efficacy_modifier": 1.0,
            },
            "CYP2C9_intermediate+VKORC1_high_sensitivity": {
                "weekly_dose_mg": 21, "action": "dose_reduction", "efficacy_modifier": 1.0,
            },
            "CYP2C9_poor+VKORC1_any": {
                "weekly_dose_mg": 14, "action": "significant_dose_reduction",
                "toxicity_risk": "high_bleeding",
            },
        }
    },
    "simvastatin": {
        "primary_gene": "SLCO1B1",
        "cpic_tier": "A",
        "mechanism": "SLCO1B1 encodes hepatic transporter OATP1B1. Reduced function → elevated simvastatin plasma levels → myopathy/rhabdomyolysis.",
        "recommendations": {
            "normal_function": {
                "action": "standard_dosing",
                "reason": "Normal hepatic uptake — standard simvastatin safe.",
                "efficacy_modifier": 1.0,
                "toxicity_risk": "low",
            },
            "intermediate_function": {
                "action": "use_lower_dose",
                "reason": "Moderately elevated plasma levels — avoid >20mg/day simvastatin.",
                "alternative": "Pravastatin or rosuvastatin (not SLCO1B1-dependent).",
                "efficacy_modifier": 0.8,
                "toxicity_risk": "moderate_myopathy",
            },
            "low_function": {
                "action": "avoid_high_doses",
                "reason": "High simvastatin plasma levels — significant myopathy/rhabdomyolysis risk.",
                "alternative": "Switch to pravastatin, rosuvastatin, or fluvastatin.",
                "efficacy_modifier": 0.6,
                "toxicity_risk": "high_myopathy",
            },
        }
    },
    "5-fluorouracil": {
        "primary_gene": "DPYD",
        "cpic_tier": "A",
        "mechanism": "DPYD encodes DPD, which catabolizes >80% of 5-FU. Deficient DPD → 5-FU accumulation → severe/fatal toxicity.",
        "recommendations": {
            "normal_activity": {
                "action": "standard_dosing",
                "reason": "Normal DPD — standard 5-FU dosing safe.",
                "efficacy_modifier": 1.0,
                "toxicity_risk": "standard",
            },
            "intermediate_activity": {
                "action": "reduce_dose_50pct",
                "reason": "~50% DPD activity — start at 50% dose, titrate based on toxicity.",
                "efficacy_modifier": 0.9,
                "toxicity_risk": "moderate_without_dose_reduction",
            },
            "low_activity": {
                "action": "contraindicated",
                "reason": "Near-absent DPD — 5-FU/capecitabine at any dose risks fatal toxicity.",
                "alternative": "Alternative chemotherapy (non-fluoropyrimidine).",
                "efficacy_modifier": 0.0,
                "toxicity_risk": "fatal",
            },
        }
    },
    "capecitabine": {
        "primary_gene": "DPYD",
        "cpic_tier": "A",
        "mechanism": "Capecitabine is a prodrug converted to 5-FU. Same DPYD dependency applies.",
        "recommendations": {
            "normal_activity": {"action": "standard_dosing", "efficacy_modifier": 1.0, "toxicity_risk": "standard"},
            "intermediate_activity": {"action": "reduce_dose_50pct", "efficacy_modifier": 0.9, "toxicity_risk": "moderate"},
            "low_activity": {"action": "contraindicated", "efficacy_modifier": 0.0, "toxicity_risk": "fatal"},
        }
    },
    "azathioprine": {
        "primary_gene": "TPMT",
        "secondary_genes": ["NUDT15"],
        "cpic_tier": "A",
        "mechanism": "TPMT methylates thiopurines. Low TPMT → accumulation of toxic thioguanine nucleotides → myelosuppression.",
        "recommendations": {
            "normal_activity": {
                "action": "standard_dosing", "efficacy_modifier": 1.0, "toxicity_risk": "standard",
            },
            "intermediate_activity": {
                "action": "reduce_dose_30_70pct",
                "reason": "Intermediate TPMT — reduce dose by 30-70% to avoid myelosuppression.",
                "efficacy_modifier": 0.85,
                "toxicity_risk": "moderate_without_adjustment",
            },
            "low_activity": {
                "action": "reduce_drastically_or_avoid",
                "reason": "Low/absent TPMT — life-threatening myelosuppression at standard doses.",
                "alternative": "Non-thiopurine immunosuppressant or 10-fold dose reduction.",
                "efficacy_modifier": 0.0,
                "toxicity_risk": "fatal_myelosuppression",
            },
        }
    },
    "omeprazole": {
        "primary_gene": "CYP2C19",
        "cpic_tier": "A",
        "mechanism": "CYP2C19 metabolizes PPIs. Poor metabolizers have 5-10x higher AUC → better acid suppression. Ultrarapid metabolizers may have therapeutic failure.",
        "recommendations": {
            "poor_metabolizer": {
                "action": "reduce_dose_or_standard",
                "reason": "Higher drug exposure — may achieve better H.pylori eradication but watch for side effects.",
                "efficacy_modifier": 1.4,
                "toxicity_risk": "mild_elevated",
            },
            "intermediate_metabolizer": {
                "action": "standard_dosing", "efficacy_modifier": 1.15, "toxicity_risk": "low",
            },
            "normal_metabolizer": {
                "action": "standard_dosing", "efficacy_modifier": 1.0, "toxicity_risk": "standard",
            },
            "rapid_metabolizer": {
                "action": "consider_dose_increase",
                "reason": "Faster metabolism — may need higher dose for H.pylori eradication.",
                "efficacy_modifier": 0.8,
                "toxicity_risk": "low",
            },
            "ultrarapid_metabolizer": {
                "action": "increase_dose",
                "reason": "Very fast CYP2C19 — standard dose may be insufficient for acid control.",
                "efficacy_modifier": 0.55,
                "toxicity_risk": "therapeutic_failure",
            },
        }
    },
    "amitriptyline": {
        "primary_gene": "CYP2D6",
        "secondary_genes": ["CYP2C19"],
        "cpic_tier": "A",
        "mechanism": "CYP2D6 metabolizes amitriptyline to nortriptyline; CYP2C19 demethylates to nortriptyline. Both affect TCA plasma levels.",
        "recommendations": {
            "poor_metabolizer": {
                "action": "avoid_or_reduce_50pct",
                "reason": "10-fold elevated plasma levels — cardiac arrhythmia and seizure risk.",
                "alternative": "SSRI not dependent on CYP2D6.",
                "efficacy_modifier": 0.7,
                "toxicity_risk": "high_cardiac_qtc",
            },
            "intermediate_metabolizer": {
                "action": "reduce_25_50pct",
                "reason": "Elevated plasma levels — reduce dose.",
                "efficacy_modifier": 0.85,
                "toxicity_risk": "moderate",
            },
            "normal_metabolizer": {
                "action": "standard_dosing", "efficacy_modifier": 1.0, "toxicity_risk": "standard",
            },
            "ultrarapid_metabolizer": {
                "action": "avoid",
                "reason": "Subtherapeutic levels — consider alternative antidepressant.",
                "efficacy_modifier": 0.3,
                "toxicity_risk": "therapeutic_failure",
            },
        }
    },
    "tacrolimus": {
        "primary_gene": "CYP3A5",
        "cpic_tier": "A",
        "mechanism": "CYP3A5 expressors require ~1.5-2x higher tacrolimus dose to achieve therapeutic trough levels.",
        "recommendations": {
            "expressor": {
                "action": "increase_dose_1_5x",
                "reason": "High CYP3A5 activity — standard dose will produce sub-therapeutic tacrolimus levels.",
                "efficacy_modifier": 0.6,
                "toxicity_risk": "low_but_under_immunosuppressed",
            },
            "low_expressor": {
                "action": "standard_or_slightly_increased",
                "efficacy_modifier": 0.85,
                "toxicity_risk": "low",
            },
            "non_expressor": {
                "action": "standard_dosing",
                "reason": "Low CYP3A5 — standard tacrolimus dose achieves therapeutic trough.",
                "efficacy_modifier": 1.0,
                "toxicity_risk": "standard",
            },
        }
    },
}

# ---------------------------------------------------------------------------
# ADVERSE DRUG REACTION LIBRARY — by drug × phenotype
# ---------------------------------------------------------------------------

ADR_PROFILES = {
    "codeine": {
        "poor_metabolizer": ["inadequate_analgesia", "codeine_accumulation", "nausea"],
        "ultrarapid_metabolizer": ["respiratory_depression", "excessive_sedation", "morphine_toxicity", "miosis"],
        "normal_metabolizer": ["constipation", "nausea", "drowsiness"],
    },
    "clopidogrel": {
        "poor_metabolizer": ["stent_thrombosis", "myocardial_infarction", "stroke", "therapeutic_failure"],
        "normal_metabolizer": ["bleeding", "bruising"],
    },
    "warfarin": {
        "high_sensitivity": ["major_bleeding", "INR_supratherapeutic", "hematoma"],
        "normal": ["minor_bleeding", "bruising"],
        "low_sensitivity": ["subtherapeutic_INR", "thrombosis"],
    },
    "5-fluorouracil": {
        "low_activity": ["grade_4_mucositis", "severe_diarrhea", "myelosuppression", "fatal_toxicity", "hand_foot_syndrome"],
        "intermediate_activity": ["grade_2_3_mucositis", "neutropenia", "diarrhea"],
        "normal_activity": ["mild_mucositis", "nausea", "fatigue"],
    },
    "azathioprine": {
        "low_activity": ["severe_myelosuppression", "pancytopenia", "infection", "fatal_aplasia"],
        "intermediate_activity": ["moderate_neutropenia", "thrombocytopenia"],
        "normal_activity": ["mild_nausea", "hepatotoxicity_rare"],
    },
    "simvastatin": {
        "low_function": ["myopathy", "rhabdomyolysis", "elevated_CK", "myalgia", "renal_failure"],
        "intermediate_function": ["myalgia", "elevated_CK"],
        "normal_function": ["mild_myalgia_rare"],
    },
}

# ---------------------------------------------------------------------------
# POPULATION FREQUENCY TABLE — for cohort simulation seeding
# ---------------------------------------------------------------------------

POPULATION_ALLELE_FREQUENCIES = {
    "European": {
        "CYP2D6_poor_metabolizer": 0.07,
        "CYP2D6_intermediate_metabolizer": 0.10,
        "CYP2D6_normal_metabolizer": 0.78,
        "CYP2D6_ultrarapid_metabolizer": 0.05,
        "CYP2C19_poor_metabolizer": 0.02,
        "CYP2C19_intermediate_metabolizer": 0.26,
        "CYP2C19_normal_metabolizer": 0.50,
        "CYP2C19_rapid_metabolizer": 0.18,
        "CYP2C19_ultrarapid_metabolizer": 0.04,
        "DPYD_low_activity": 0.005,
        "DPYD_intermediate_activity": 0.035,
        "DPYD_normal_activity": 0.96,
        "TPMT_low_activity": 0.01,
        "TPMT_intermediate_activity": 0.10,
        "TPMT_normal_activity": 0.89,
        "SLCO1B1_low_function": 0.04,
        "SLCO1B1_intermediate_function": 0.24,
        "SLCO1B1_normal_function": 0.72,
    },
    "East_Asian": {
        "CYP2D6_poor_metabolizer": 0.01,
        "CYP2D6_intermediate_metabolizer": 0.50,
        "CYP2D6_normal_metabolizer": 0.46,
        "CYP2D6_ultrarapid_metabolizer": 0.01,
        "CYP2C19_poor_metabolizer": 0.15,
        "CYP2C19_intermediate_metabolizer": 0.40,
        "CYP2C19_normal_metabolizer": 0.42,
        "CYP2C19_rapid_metabolizer": 0.03,
        "CYP2C19_ultrarapid_metabolizer": 0.001,
        "DPYD_low_activity": 0.001,
        "DPYD_intermediate_activity": 0.01,
        "DPYD_normal_activity": 0.989,
        "TPMT_low_activity": 0.002,
        "TPMT_intermediate_activity": 0.04,
        "TPMT_normal_activity": 0.958,
        "SLCO1B1_low_function": 0.14,
        "SLCO1B1_intermediate_function": 0.38,
        "SLCO1B1_normal_function": 0.48,
    },
    "African": {
        "CYP2D6_poor_metabolizer": 0.02,
        "CYP2D6_intermediate_metabolizer": 0.35,
        "CYP2D6_normal_metabolizer": 0.45,
        "CYP2D6_ultrarapid_metabolizer": 0.29,  # Much higher in African populations
        "CYP2C19_poor_metabolizer": 0.04,
        "CYP2C19_intermediate_metabolizer": 0.32,
        "CYP2C19_normal_metabolizer": 0.55,
        "CYP2C19_rapid_metabolizer": 0.07,
        "CYP2C19_ultrarapid_metabolizer": 0.02,
        "DPYD_low_activity": 0.003,
        "DPYD_intermediate_activity": 0.02,
        "DPYD_normal_activity": 0.977,
        "TPMT_low_activity": 0.005,
        "TPMT_intermediate_activity": 0.08,
        "TPMT_normal_activity": 0.915,
        "SLCO1B1_low_function": 0.02,
        "SLCO1B1_intermediate_function": 0.15,
        "SLCO1B1_normal_function": 0.83,
    },
}

# All SNPs relevant to pharmacogenomics (subset for fast lookup)
PGX_RELEVANT_SNPS = set(SNP_DATABASE.keys())

# Genes covered by this system
COVERED_GENES = {"CYP2D6", "CYP2C19", "CYP2C9", "VKORC1", "DPYD", "TPMT",
                 "SLCO1B1", "CYP3A5", "UGT1A1", "MTHFR", "CYP1A2"}

# Drugs available for simulation
AVAILABLE_DRUGS = list(DRUG_GENE_PAIRS.keys())
