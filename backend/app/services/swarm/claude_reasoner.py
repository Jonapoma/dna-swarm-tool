"""
Claude API reasoner — uses Anthropic Claude to simulate individual
patient responses in the context of their pharmacogenomic profile.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

import anthropic

from app.utils.logger import get_logger

logger = get_logger("genomicswarm.claude")


OUTCOME_SYSTEM_PROMPT = """You are a clinical pharmacology simulation engine embedded in a drug trial prediction system.

Your role: Given a patient's pharmacogenomic (PGx) profile and a drug administration event, predict the clinical outcome.

Rules:
- Base your prediction on the PGx data — it is scientifically grounded in CPIC guidelines
- Be realistic: not every poor metabolizer has a catastrophic outcome; stochastic variation exists
- Poor metabolizers of prodrugs (codeine, clopidogrel) should show reduced efficacy
- Ultrarapid metabolizers of prodrugs may show toxicity or paradoxically reduced duration
- Always return valid JSON exactly as specified
- Use clinical language appropriate for a CRO medical monitor
- Adverse events should match the patient's risk profile
- Consider age and weight when relevant (elderly patients: higher toxicity risk)"""

OUTCOME_USER_TEMPLATE = """PATIENT PROFILE:
{agent_description}

TRIAL CONFIGURATION:
- Drug: {drug} {dose_mg}mg
- Route: {route}
- Duration: {duration_days} days
- Indication: {indication}
- Comparator: {comparator}

PHARMACOKINETIC CONTEXT:
- Gene: {gene} | Phenotype: {phenotype}
- Relative drug exposure vs. normal: {relative_exposure:.1f}x
- Predicted AUC ratio: {auc_ratio:.2f}
- CPIC recommendation: {recommendation}
- Mechanism: {mechanism}

Simulate this patient's clinical response. Return ONLY valid JSON with this exact structure:
{{
  "efficacy_score": <integer 0-10, where 10=full response, 0=no response>,
  "response_category": "<full_response|partial_response|no_response|toxic_response|adverse_event_only>",
  "adverse_events": [<list of specific ADR strings, empty if none>],
  "plasma_level_category": "<sub_therapeutic|therapeutic|supra_therapeutic>",
  "time_to_effect_days": <number or null>,
  "dose_adjustment_needed": <true|false>,
  "suggested_dose_adjustment": "<increase_25pct|increase_50pct|decrease_25pct|decrease_50pct|discontinue|none>",
  "clinical_narrative": "<2-3 sentences describing the patient's clinical course>",
  "trial_endpoint_met": <true|false>,
  "discontinuation_reason": "<string or null>",
  "confidence": "<high|medium|low>"
}}"""


POPULATION_SYSTEM_PROMPT = """You are a biostatistics AI analysing drug trial simulation results.
Summarise population-level findings from individual agent outcomes.
Focus on: subpopulation differences by PGx phenotype, statistical patterns, clinical significance.
Return clean, structured analysis suitable for a pharma medical affairs audience."""


class ClaudeReasoner:
    """Wraps Anthropic Claude API for patient-level and population-level reasoning."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    # -----------------------------------------------------------------------
    # Patient-level outcome prediction
    # -----------------------------------------------------------------------

    def predict_patient_outcome(
        self,
        persona: dict,
        trial_config: dict,
    ) -> dict:
        """
        Call Claude to simulate a single patient's drug trial outcome.
        Returns structured outcome dict.
        """
        pk_pd = persona.get("pk_pd", {})

        user_msg = OUTCOME_USER_TEMPLATE.format(
            agent_description=persona.get("agent_description", "No description"),
            drug=trial_config.get("drug", "Unknown"),
            dose_mg=trial_config.get("dose_mg", 0),
            route=trial_config.get("route", "oral"),
            duration_days=trial_config.get("duration_days", 28),
            indication=trial_config.get("indication", "unspecified"),
            comparator=trial_config.get("comparator", "placebo"),
            gene=pk_pd.get("gene", "unknown"),
            phenotype=pk_pd.get("phenotype", "unknown").replace("_", " "),
            relative_exposure=pk_pd.get("relative_exposure", 1.0),
            auc_ratio=pk_pd.get("predicted_auc_ratio", 1.0),
            recommendation=pk_pd.get("recommendation", "standard_dosing").replace("_", " "),
            mechanism=pk_pd.get("mechanism", "unknown"),
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                system=OUTCOME_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            )
            raw_text = response.content[0].text
            outcome = self._parse_json_response(raw_text)
            outcome["_raw"] = raw_text
            outcome["_tokens_used"] = response.usage.input_tokens + response.usage.output_tokens
        except anthropic.APIError as e:
            logger.error(f"Claude API error for {persona['id']}: {e}")
            outcome = self._fallback_outcome(persona, pk_pd)
        except Exception as e:
            logger.error(f"Unexpected error for {persona['id']}: {e}")
            outcome = self._fallback_outcome(persona, pk_pd)

        return outcome

    # -----------------------------------------------------------------------
    # Population-level analysis
    # -----------------------------------------------------------------------

    def analyse_population(
        self,
        agent_results: List[dict],
        trial_config: dict,
        stats: dict,
    ) -> str:
        """
        Generate a natural-language population analysis from aggregated results.
        Returns markdown-formatted report section.
        """
        drug = trial_config.get("drug", "drug")
        n = len(agent_results)

        # Build summary table for Claude
        phenotype_summary = {}
        for result in agent_results:
            phen = result.get("phenotype", "unknown")
            if phen not in phenotype_summary:
                phenotype_summary[phen] = {"n": 0, "efficacy_sum": 0, "adverse_events": 0, "discontinued": 0}
            phenotype_summary[phen]["n"] += 1
            phenotype_summary[phen]["efficacy_sum"] += result.get("efficacy_score", 5)
            if result.get("adverse_events"):
                phenotype_summary[phen]["adverse_events"] += 1
            if result.get("discontinuation_reason"):
                phenotype_summary[phen]["discontinued"] += 1

        # Compute averages
        for phen, data in phenotype_summary.items():
            if data["n"] > 0:
                data["mean_efficacy"] = round(data["efficacy_sum"] / data["n"], 2)
                data["adr_rate_pct"] = round(100 * data["adverse_events"] / data["n"], 1)
                data["discontinuation_rate_pct"] = round(100 * data["discontinued"] / data["n"], 1)

        prompt = f"""Drug trial simulation results for {drug} ({n} virtual patients):

Overall statistics:
{json.dumps(stats, indent=2)}

Breakdown by PGx phenotype:
{json.dumps(phenotype_summary, indent=2)}

Trial configuration:
{json.dumps(trial_config, indent=2)}

Write a concise population-level analysis (400-600 words) covering:
1. Overall efficacy and safety findings
2. PGx subpopulation differences and their clinical significance
3. Patients at highest risk (ADRs, therapeutic failure)
4. CPIC-guided dose/drug recommendations for the identified subpopulations
5. Key insight for pharma/CRO audience: what does this simulation suggest about trial enrichment strategy?

Format in clean markdown with section headers."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=POPULATION_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Population analysis error: {e}")
            return f"*Population analysis unavailable: {e}*"

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _parse_json_response(self, text: str) -> dict:
        """Extract and parse JSON from Claude response (handles markdown fences)."""
        # Strip markdown code fences
        text = re.sub(r"```(?:json)?\s*", "", text).strip()
        text = text.rstrip("`").strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON object with regex
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group())
                except json.JSONDecodeError:
                    pass

        logger.warning("Failed to parse Claude JSON response, using defaults")
        return {
            "efficacy_score": 5,
            "response_category": "partial_response",
            "adverse_events": [],
            "plasma_level_category": "therapeutic",
            "time_to_effect_days": None,
            "dose_adjustment_needed": False,
            "suggested_dose_adjustment": "none",
            "clinical_narrative": "Simulation data unavailable — default response assigned.",
            "trial_endpoint_met": True,
            "discontinuation_reason": None,
            "confidence": "low",
            "_parse_error": True,
        }

    def _fallback_outcome(self, persona: dict, pk_pd: dict) -> dict:
        """
        Deterministic fallback outcome when Claude API is unavailable.
        Based purely on PGx efficacy modifier — no LLM reasoning.
        """
        eff_mod = pk_pd.get("efficacy_modifier", 1.0)
        rec = pk_pd.get("recommendation", "standard_dosing")
        adrs = pk_pd.get("expected_adrs", [])

        if rec == "contraindicated" or eff_mod == 0.0:
            return {
                "efficacy_score": 0,
                "response_category": "adverse_event_only",
                "adverse_events": adrs[:3],
                "plasma_level_category": "supra_therapeutic",
                "time_to_effect_days": None,
                "dose_adjustment_needed": True,
                "suggested_dose_adjustment": "discontinue",
                "clinical_narrative": "Drug contraindicated based on PGx profile. Fallback deterministic result.",
                "trial_endpoint_met": False,
                "discontinuation_reason": "pgx_contraindication",
                "confidence": "high",
                "_fallback": True,
            }
        elif eff_mod < 0.3:
            efficacy_score = 1
            category = "no_response"
        elif eff_mod < 0.7:
            efficacy_score = 4
            category = "partial_response"
        elif eff_mod < 1.2:
            efficacy_score = 7
            category = "full_response"
        else:
            efficacy_score = 7
            category = "full_response"

        return {
            "efficacy_score": efficacy_score,
            "response_category": category,
            "adverse_events": adrs[:2] if adrs else [],
            "plasma_level_category": "therapeutic",
            "time_to_effect_days": 7,
            "dose_adjustment_needed": rec not in ("standard_dosing", ""),
            "suggested_dose_adjustment": "none",
            "clinical_narrative": f"Fallback deterministic result. Efficacy modifier: {eff_mod:.2f}.",
            "trial_endpoint_met": efficacy_score >= 5,
            "discontinuation_reason": None,
            "confidence": "medium",
            "_fallback": True,
        }
