"""
Genomic file parsers: 23andMe TSV and VCF formats.
Outputs a normalised genome dict: { rsid: genotype_string }
"""

from __future__ import annotations

import io
import re
from typing import IO, Dict, Optional, Tuple

from app.utils.logger import get_logger

logger = get_logger("genomicswarm.parsers")

# Genotype string (e.g. "AG", "AA", "--")
GenomeDict = Dict[str, str]


# ---------------------------------------------------------------------------
# 23andMe / AncestryDNA TSV parser
# ---------------------------------------------------------------------------

def parse_23andme(file_obj: IO[bytes], encoding: str = "utf-8") -> Tuple[GenomeDict, dict]:
    """
    Parse a 23andMe / AncestryDNA raw DNA file.

    Expected format (tab-separated, lines starting with # are comments):
        # rsid    chromosome    position    genotype
        rs4477212 1             82154       AA
        rs3094315 1             752566      AG
        ...

    Returns (genome_dict, metadata)
    """
    genome: GenomeDict = {}
    metadata: dict = {"format": "23andme", "snp_count": 0, "no_call_count": 0}

    if isinstance(file_obj.read(0), bytes):
        raw = file_obj.read()
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
    else:
        text = file_obj.read()

    provider = "23andMe"
    build = "unknown"

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith("#"):
            low = line.lower()
            if "ancestry" in low:
                provider = "AncestryDNA"
            elif "myheritage" in low:
                provider = "MyHeritage"
            if "grch38" in low or "hg38" in low:
                build = "GRCh38"
            elif "grch37" in low or "hg19" in low:
                build = "GRCh37"
            continue

        parts = line.split()
        if len(parts) < 4:
            continue

        rsid, _chrom, _pos, genotype = parts[0], parts[1], parts[2], parts[3]

        if not rsid.startswith("rs"):
            continue

        # Normalise: uppercase, sort alleles ("GA" → "AG")
        genotype = genotype.upper().replace("-", "")
        if len(genotype) == 2:
            genotype = "".join(sorted(genotype))
            genome[rsid] = genotype
        elif len(genotype) == 0 or genotype in ("--", "00", "II", "DD"):
            metadata["no_call_count"] += 1
        else:
            genome[rsid] = genotype  # indels / hemi / MT

    metadata["snp_count"] = len(genome)
    metadata["provider"] = provider
    metadata["build"] = build
    logger.info(f"Parsed {metadata['snp_count']} SNPs from {provider} file (build {build})")
    return genome, metadata


# ---------------------------------------------------------------------------
# VCF parser (v4.x)
# ---------------------------------------------------------------------------

def parse_vcf(file_obj: IO[bytes], sample_index: int = 0) -> Tuple[GenomeDict, dict]:
    """
    Parse a VCF file (single sample or first sample from multi-sample).
    Handles gzipped VCF via caller pre-decompression.

    Returns (genome_dict, metadata)
    """
    genome: GenomeDict = {}
    metadata: dict = {"format": "vcf", "snp_count": 0, "sample_id": None, "build": "unknown"}

    if isinstance(file_obj.read(0), bytes):
        raw = file_obj.read()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
    else:
        text = file_obj.read()

    sample_names: list = []
    ref_map: Dict[str, str] = {}  # rsid → REF allele for orientation

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith("##"):
            low = line.lower()
            if "grch38" in low or "hg38" in low:
                metadata["build"] = "GRCh38"
            elif "grch37" in low or "hg19" in low:
                metadata["build"] = "GRCh37"
            continue

        if line.startswith("#CHROM"):
            # Header line with sample names
            parts = line.lstrip("#").split("\t")
            # FORMAT field is index 8, samples start at 9
            if len(parts) > 9:
                sample_names = parts[9:]
                if sample_index < len(sample_names):
                    metadata["sample_id"] = sample_names[sample_index]
            continue

        # Data line
        parts = line.split("\t")
        if len(parts) < 10:
            continue

        chrom, pos, vid, ref, alt, qual, filt, info, fmt = parts[:9]
        sample_fields = parts[9:]

        if sample_index >= len(sample_fields):
            continue

        # Extract rsID
        rsid = None
        if vid.startswith("rs"):
            rsid = vid
        else:
            # Try to find rsID in INFO field
            m = re.search(r"RS=(\d+)", info)
            if m:
                rsid = f"rs{m.group(1)}"

        if not rsid:
            continue

        # Parse genotype from FORMAT/SAMPLE
        fmt_fields = fmt.split(":")
        if "GT" not in fmt_fields:
            continue

        gt_idx = fmt_fields.index("GT")
        sample_vals = sample_fields[sample_index].split(":")
        if gt_idx >= len(sample_vals):
            continue

        gt_raw = sample_vals[gt_idx]
        # GT can be "0/1", "1|0", "0/0", "./.", etc.
        separator = "|" if "|" in gt_raw else "/"
        allele_codes = gt_raw.split(separator)

        if "." in allele_codes:
            metadata["no_call_count"] = metadata.get("no_call_count", 0) + 1
            continue

        all_alleles = [ref] + alt.split(",")
        try:
            alleles = [all_alleles[int(c)] for c in allele_codes]
        except (IndexError, ValueError):
            continue

        # Build genotype string (only for SNPs — single-char alleles)
        alleles = [a for a in alleles if len(a) == 1]
        if len(alleles) == 2:
            genotype = "".join(sorted(alleles)).upper()
            genome[rsid] = genotype

    metadata["snp_count"] = len(genome)
    logger.info(f"Parsed {metadata['snp_count']} SNPs from VCF (build {metadata['build']})")
    return genome, metadata


# ---------------------------------------------------------------------------
# Cohort parser — multiple samples from a single multi-sample VCF
# ---------------------------------------------------------------------------

def parse_vcf_cohort(file_obj: IO[bytes]) -> Tuple[Dict[str, GenomeDict], dict]:
    """
    Parse a multi-sample VCF and return a dict of sample_id → genome_dict.
    """
    if isinstance(file_obj.read(0), bytes):
        raw = file_obj.read()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
    else:
        text = file_obj.read()

    sample_names: list = []
    cohort: Dict[str, GenomeDict] = {}
    metadata: dict = {"format": "vcf_cohort", "sample_count": 0, "snp_count": 0, "build": "unknown"}

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith("##"):
            low = line.lower()
            if "grch38" in low or "hg38" in low:
                metadata["build"] = "GRCh38"
            elif "grch37" in low or "hg19" in low:
                metadata["build"] = "GRCh37"
            continue

        if line.startswith("#CHROM"):
            parts = line.lstrip("#").split("\t")
            if len(parts) > 9:
                sample_names = parts[9:]
                cohort = {name: {} for name in sample_names}
            continue

        parts = line.split("\t")
        if len(parts) < 9 + len(sample_names):
            continue

        chrom, pos, vid, ref, alt, qual, filt, info, fmt = parts[:9]
        sample_fields = parts[9:]

        rsid = vid if vid.startswith("rs") else None
        if not rsid:
            m = re.search(r"RS=(\d+)", info)
            if m:
                rsid = f"rs{m.group(1)}"
        if not rsid:
            continue

        fmt_fields = fmt.split(":")
        if "GT" not in fmt_fields:
            continue
        gt_idx = fmt_fields.index("GT")
        all_alleles = [ref] + alt.split(",")

        for i, sample_id in enumerate(sample_names):
            if i >= len(sample_fields):
                continue
            sample_vals = sample_fields[i].split(":")
            if gt_idx >= len(sample_vals):
                continue
            gt_raw = sample_vals[gt_idx]
            sep = "|" if "|" in gt_raw else "/"
            allele_codes = gt_raw.split(sep)
            if "." in allele_codes:
                continue
            try:
                alleles = [all_alleles[int(c)] for c in allele_codes]
            except (IndexError, ValueError):
                continue
            alleles = [a for a in alleles if len(a) == 1]
            if len(alleles) == 2:
                cohort[sample_id][rsid] = "".join(sorted(alleles)).upper()

    metadata["sample_count"] = len(sample_names)
    snp_counts = [len(v) for v in cohort.values()]
    metadata["snp_count"] = int(sum(snp_counts) / len(snp_counts)) if snp_counts else 0
    logger.info(f"Parsed cohort VCF: {metadata['sample_count']} samples, avg {metadata['snp_count']} SNPs/sample")
    return cohort, metadata


# ---------------------------------------------------------------------------
# Dispatcher — auto-detect file type
# ---------------------------------------------------------------------------

def parse_genome_file(filename: str, file_bytes: bytes) -> Tuple[GenomeDict, dict]:
    """Auto-detect format and parse a single-sample genome file."""
    name_lower = filename.lower()
    buf = io.BytesIO(file_bytes)

    if name_lower.endswith(".vcf") or name_lower.endswith(".vcf.gz"):
        return parse_vcf(buf)

    # Default: 23andMe / AncestryDNA TSV
    return parse_23andme(buf)


def parse_cohort_file(filename: str, file_bytes: bytes) -> Tuple[Dict[str, GenomeDict], dict]:
    """Parse a multi-sample VCF cohort file."""
    buf = io.BytesIO(file_bytes)
    return parse_vcf_cohort(buf)
