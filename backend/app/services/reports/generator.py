"""
Report generator — produces structured HTML and JSON reports
from simulation results.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List

from app.utils.logger import get_logger

logger = get_logger("genomicswarm.report")


def generate_html_report(simulation: dict) -> str:
    """Generate a self-contained HTML report from simulation results."""
    trial = simulation.get("trial_config", {})
    stats = simulation.get("statistics", {})
    results = simulation.get("agent_results", [])
    analysis = simulation.get("population_analysis", "No analysis generated.")
    sim_id = simulation.get("id", "unknown")
    started = simulation.get("started_at", "")
    completed = simulation.get("completed_at", "")

    drug = trial.get("drug", "Unknown")
    dose = trial.get("dose_mg", 0)
    n = stats.get("total_agents", len(results))
    mean_eff = stats.get("mean_efficacy_score", 0)
    response_rate = stats.get("response_rate_pct", 0)
    adr_rate = stats.get("adr_rate_pct", 0)
    disc_rate = stats.get("discontinuation_rate_pct", 0)

    # Phenotype breakdown rows
    phen_rows = ""
    for phen, data in stats.get("phenotype_breakdown", {}).items():
        phen_display = phen.replace("_", " ").title()
        phen_rows += f"""
        <tr>
            <td>{phen_display}</td>
            <td>{data['n']}</td>
            <td>{data['mean_efficacy']}</td>
            <td>{data['response_rate_pct']}%</td>
            <td>{data['adr_rate_pct']}%</td>
            <td>{data['discontinuation_rate_pct']}%</td>
        </tr>"""

    # Top ADR rows
    adr_rows = ""
    for adr_entry in stats.get("top_adverse_events", []):
        adr_rows += f"""
        <tr>
            <td>{adr_entry['event'].replace('_', ' ')}</td>
            <td>{adr_entry['count']}</td>
            <td>{adr_entry['rate_pct']}%</td>
        </tr>"""

    # Response distribution chart data
    resp_dist = stats.get("response_distribution", {})
    resp_labels = json.dumps(list(resp_dist.keys()))
    resp_values = json.dumps(list(resp_dist.values()))

    # Efficacy by phenotype chart data
    phen_bd = stats.get("phenotype_breakdown", {})
    phen_labels = json.dumps([p.replace("_", " ") for p in phen_bd.keys()])
    phen_efficacy = json.dumps([d["mean_efficacy"] for d in phen_bd.values()])
    phen_response_rates = json.dumps([d["response_rate_pct"] for d in phen_bd.values()])

    # Convert markdown analysis to basic HTML
    analysis_html = _markdown_to_html(analysis)

    # Individual patient samples (first 20 for display)
    patient_rows = ""
    for r in results[:20]:
        adrs = ", ".join(r.get("adverse_events", [])[:3]) or "None"
        ep = "Yes" if r.get("trial_endpoint_met") else "No"
        phen_short = r.get("phenotype", "unknown").replace("_", " ")[:25]
        patient_rows += f"""
        <tr>
            <td class="mono">{r.get('patient_id', '')[:20]}</td>
            <td>{r.get('age', '')}</td>
            <td>{r.get('sex', '')}</td>
            <td>{phen_short}</td>
            <td>{r.get('efficacy_score', '')}/10</td>
            <td>{r.get('response_category', '').replace('_', ' ')}</td>
            <td>{adrs}</td>
            <td>{ep}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>GenomicSwarm Report — {drug} {dose}mg</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    :root {{
      --bg: #0d1117; --surface: #161b22; --border: #30363d;
      --text: #e6edf3; --muted: #8b949e; --accent: #58a6ff;
      --green: #3fb950; --red: #f85149; --yellow: #d29922;
      --purple: #bc8cff;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 14px; }}
    .container {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
    .header {{ border-bottom: 1px solid var(--border); padding-bottom: 20px; margin-bottom: 24px; }}
    .header h1 {{ font-size: 24px; font-weight: 600; color: var(--accent); }}
    .header .meta {{ color: var(--muted); margin-top: 6px; font-size: 13px; }}
    .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 500; }}
    .badge-green {{ background: rgba(63,185,80,0.15); color: var(--green); }}
    .badge-red {{ background: rgba(248,81,73,0.15); color: var(--red); }}
    .badge-yellow {{ background: rgba(210,153,34,0.15); color: var(--yellow); }}
    .badge-blue {{ background: rgba(88,166,255,0.15); color: var(--accent); }}
    .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }}
    .kpi {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }}
    .kpi .value {{ font-size: 28px; font-weight: 700; margin-bottom: 4px; }}
    .kpi .label {{ color: var(--muted); font-size: 12px; }}
    .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }}
    .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 20px; }}
    .card h2 {{ font-size: 15px; font-weight: 600; margin-bottom: 16px; color: var(--accent); }}
    .chart-container {{ position: relative; height: 280px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th {{ text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--border); color: var(--muted); font-weight: 500; }}
    td {{ padding: 7px 12px; border-bottom: 1px solid var(--border); }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: rgba(88,166,255,0.04); }}
    .mono {{ font-family: monospace; font-size: 12px; }}
    .analysis {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 20px; margin-bottom: 24px; line-height: 1.7; }}
    .analysis h2 {{ font-size: 15px; font-weight: 600; margin-bottom: 16px; color: var(--accent); }}
    .analysis h3 {{ font-size: 14px; font-weight: 600; margin: 16px 0 8px; color: var(--text); }}
    .analysis p {{ color: var(--muted); margin-bottom: 10px; }}
    .analysis li {{ color: var(--muted); margin-left: 20px; margin-bottom: 4px; }}
    .analysis ul, .analysis ol {{ margin-bottom: 10px; }}
    .analysis strong {{ color: var(--text); }}
    .footer {{ color: var(--muted); font-size: 12px; text-align: center; padding: 20px 0; border-top: 1px solid var(--border); margin-top: 32px; }}
    @media (max-width: 768px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>GenomicSwarm — Trial Simulation Report</h1>
    <div class="meta">
      Drug: <strong>{drug} {dose}mg</strong> &nbsp;|&nbsp;
      Agents: <strong>{n}</strong> &nbsp;|&nbsp;
      Started: <strong>{started[:19].replace('T',' ')}</strong> &nbsp;|&nbsp;
      Completed: <strong>{completed[:19].replace('T',' ') if completed else 'N/A'}</strong> &nbsp;|&nbsp;
      Simulation ID: <code style="font-size:11px">{sim_id}</code>
    </div>
  </div>

  <!-- KPI Cards -->
  <div class="kpi-grid">
    <div class="kpi">
      <div class="value" style="color:var(--accent)">{n}</div>
      <div class="label">Virtual Patients</div>
    </div>
    <div class="kpi">
      <div class="value" style="color:var(--green)">{mean_eff}/10</div>
      <div class="label">Mean Efficacy Score</div>
    </div>
    <div class="kpi">
      <div class="value" style="color:var(--green)">{response_rate}%</div>
      <div class="label">Trial Endpoint Rate</div>
    </div>
    <div class="kpi">
      <div class="value" style="color:var(--yellow)">{adr_rate}%</div>
      <div class="label">ADR Rate</div>
    </div>
    <div class="kpi">
      <div class="value" style="color:var(--red)">{disc_rate}%</div>
      <div class="label">Discontinuation Rate</div>
    </div>
    <div class="kpi">
      <div class="value" style="color:var(--purple)">{trial.get('indication','—')[:20]}</div>
      <div class="label">Indication</div>
    </div>
  </div>

  <!-- Charts -->
  <div class="grid-2">
    <div class="card">
      <h2>Response Distribution</h2>
      <div class="chart-container">
        <canvas id="responseChart"></canvas>
      </div>
    </div>
    <div class="card">
      <h2>Efficacy by PGx Phenotype</h2>
      <div class="chart-container">
        <canvas id="phenotypeChart"></canvas>
      </div>
    </div>
  </div>

  <!-- Phenotype breakdown table -->
  <div class="card" style="margin-bottom:24px">
    <h2>Phenotype Subpopulation Analysis</h2>
    <table>
      <thead>
        <tr>
          <th>Phenotype</th><th>N</th><th>Mean Efficacy</th>
          <th>Response Rate</th><th>ADR Rate</th><th>Discontinuation</th>
        </tr>
      </thead>
      <tbody>{phen_rows}</tbody>
    </table>
  </div>

  <!-- ADR table -->
  <div class="card" style="margin-bottom:24px">
    <h2>Top Adverse Events</h2>
    <table>
      <thead><tr><th>Adverse Event</th><th>Count</th><th>Rate</th></tr></thead>
      <tbody>{adr_rows if adr_rows else '<tr><td colspan="3" style="color:var(--muted)">No adverse events recorded</td></tr>'}</tbody>
    </table>
  </div>

  <!-- Claude Population Analysis -->
  <div class="analysis">
    <h2>AI Population Analysis</h2>
    {analysis_html}
  </div>

  <!-- Patient sample table -->
  <div class="card" style="margin-bottom:24px">
    <h2>Patient Sample (first 20)</h2>
    <div style="overflow-x:auto">
    <table>
      <thead>
        <tr><th>Patient ID</th><th>Age</th><th>Sex</th><th>Phenotype</th>
        <th>Efficacy</th><th>Response</th><th>ADRs</th><th>Endpoint</th></tr>
      </thead>
      <tbody>{patient_rows}</tbody>
    </table>
    </div>
  </div>

  <div class="footer">
    Generated by GenomicSwarm &nbsp;|&nbsp; CPIC Tier A evidence &nbsp;|&nbsp;
    For research use only. Not for clinical decision-making.
  </div>
</div>

<script>
const palette = ['#58a6ff','#3fb950','#f85149','#d29922','#bc8cff','#79c0ff','#56d364'];

// Response distribution pie
new Chart(document.getElementById('responseChart'), {{
  type: 'doughnut',
  data: {{
    labels: {resp_labels},
    datasets: [{{ data: {resp_values}, backgroundColor: palette, borderWidth: 0 }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{
      legend: {{ position: 'bottom', labels: {{ color: '#8b949e', font: {{ size: 11 }} }} }}
    }}
  }}
}});

// Efficacy by phenotype bar chart
new Chart(document.getElementById('phenotypeChart'), {{
  type: 'bar',
  data: {{
    labels: {phen_labels},
    datasets: [
      {{
        label: 'Mean Efficacy',
        data: {phen_efficacy},
        backgroundColor: 'rgba(88,166,255,0.7)',
        yAxisID: 'y'
      }},
      {{
        label: 'Response Rate %',
        data: {phen_response_rates},
        backgroundColor: 'rgba(63,185,80,0.7)',
        yAxisID: 'y1'
      }}
    ]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ labels: {{ color: '#8b949e', font: {{ size: 11 }} }} }} }},
    scales: {{
      x: {{ ticks: {{ color: '#8b949e', font: {{ size: 10 }} }}, grid: {{ color: '#30363d' }} }},
      y: {{ ticks: {{ color: '#8b949e' }}, grid: {{ color: '#30363d' }}, max: 10, title: {{ display: true, text: 'Efficacy', color: '#8b949e' }} }},
      y1: {{ position: 'right', ticks: {{ color: '#8b949e' }}, grid: {{ display: false }}, max: 100, title: {{ display: true, text: 'Response %', color: '#8b949e' }} }}
    }}
  }}
}});
</script>
</body>
</html>"""


def generate_json_report(simulation: dict) -> dict:
    """Return a clean JSON-serialisable summary (no raw agent blobs)."""
    trial = simulation.get("trial_config", {})
    stats = simulation.get("statistics", {})

    return {
        "simulation_id": simulation.get("id"),
        "status": simulation.get("status"),
        "started_at": simulation.get("started_at"),
        "completed_at": simulation.get("completed_at"),
        "trial_config": trial,
        "statistics": stats,
        "population_analysis": simulation.get("population_analysis"),
        "generated_at": datetime.utcnow().isoformat(),
        "version": "1.0",
        "disclaimer": "For research use only. Not for clinical decision-making.",
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _markdown_to_html(md: str) -> str:
    """Very basic markdown → HTML converter (no external dependency)."""
    import re
    lines = md.split("\n")
    out = []
    in_list = False

    for line in lines:
        if line.startswith("### "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("## "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h3>{line[3:]}</h3>")
        elif line.startswith("# "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h3>{line[2:]}</h3>")
        elif line.startswith("- ") or line.startswith("* "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            content = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", line[2:])
            out.append(f"<li>{content}</li>")
        elif line.strip() == "":
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append("")
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            content = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", line)
            out.append(f"<p>{content}</p>")

    if in_list:
        out.append("</ul>")

    return "\n".join(out)
