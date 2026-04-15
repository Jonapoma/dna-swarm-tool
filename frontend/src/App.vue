<template>
  <div id="gs-app">
    <nav class="navbar">
      <div class="nav-brand">
        <span class="dna-icon">🧬</span>
        <span class="brand-name">Genomic<strong>Swarm</strong></span>
        <span class="brand-tag">PGx Drug Trial Simulator</span>
      </div>
      <div class="nav-links">
        <router-link to="/" class="nav-link">New Simulation</router-link>
        <a href="https://cpicpgx.org" target="_blank" class="nav-link muted">CPIC Guidelines ↗</a>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
    <footer class="app-footer">
      GenomicSwarm v1.0 &nbsp;·&nbsp; CPIC Tier A evidence &nbsp;·&nbsp;
      For research use only. Not for clinical decision-making.
    </footer>
  </div>
</template>

<style>
:root {
  --bg: #0d1117;
  --surface: #161b22;
  --surface2: #1c2128;
  --border: #30363d;
  --text: #e6edf3;
  --muted: #8b949e;
  --accent: #58a6ff;
  --accent-dim: rgba(88,166,255,0.12);
  --green: #3fb950;
  --red: #f85149;
  --yellow: #d29922;
  --purple: #bc8cff;
  --orange: #ffa657;
  --radius: 8px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
  font-size: 14px;
  line-height: 1.5;
  min-height: 100vh;
}
#gs-app { display: flex; flex-direction: column; min-height: 100vh; }

.navbar {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 0 24px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky; top: 0; z-index: 100;
}
.nav-brand { display: flex; align-items: center; gap: 10px; }
.dna-icon { font-size: 20px; }
.brand-name { font-size: 16px; color: var(--text); }
.brand-name strong { color: var(--accent); }
.brand-tag {
  font-size: 11px; color: var(--muted);
  background: var(--accent-dim); border: 1px solid var(--accent);
  padding: 2px 8px; border-radius: 12px;
}
.nav-links { display: flex; gap: 16px; }
.nav-link {
  color: var(--muted); text-decoration: none; font-size: 13px;
  transition: color .15s;
}
.nav-link:hover { color: var(--text); }
.nav-link.router-link-active { color: var(--accent); }
.nav-link.muted { color: var(--muted); }

.main-content { flex: 1; padding: 24px; max-width: 1200px; margin: 0 auto; width: 100%; }
.app-footer {
  text-align: center; color: var(--muted); font-size: 11px;
  padding: 16px; border-top: 1px solid var(--border);
}

/* Shared utility classes */
.card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 20px;
}
.btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 16px; border-radius: 6px; font-size: 13px;
  font-weight: 500; cursor: pointer; border: none; transition: all .15s;
}
.btn-primary { background: var(--accent); color: #0d1117; }
.btn-primary:hover { background: #79c0ff; }
.btn-primary:disabled { background: var(--border); color: var(--muted); cursor: not-allowed; }
.btn-secondary { background: var(--surface2); color: var(--text); border: 1px solid var(--border); }
.btn-secondary:hover { border-color: var(--accent); color: var(--accent); }
.btn-danger { background: rgba(248,81,73,0.15); color: var(--red); border: 1px solid var(--red); }

.badge {
  display: inline-block; padding: 2px 8px; border-radius: 12px;
  font-size: 11px; font-weight: 500;
}
.badge-green { background: rgba(63,185,80,0.15); color: var(--green); }
.badge-red { background: rgba(248,81,73,0.15); color: var(--red); }
.badge-yellow { background: rgba(210,153,34,0.15); color: var(--yellow); }
.badge-blue { background: rgba(88,166,255,0.15); color: var(--accent); }
.badge-purple { background: rgba(188,140,255,0.15); color: var(--purple); }

.form-group { margin-bottom: 16px; }
.form-label { display: block; font-size: 12px; font-weight: 500; color: var(--muted); margin-bottom: 6px; }
.form-input, .form-select {
  width: 100%; padding: 8px 12px; background: var(--surface2);
  border: 1px solid var(--border); border-radius: 6px;
  color: var(--text); font-size: 13px; outline: none;
  transition: border-color .15s;
}
.form-input:focus, .form-select:focus { border-color: var(--accent); }
.form-select option { background: var(--surface2); }

.section-title {
  font-size: 16px; font-weight: 600; color: var(--text);
  margin-bottom: 16px; display: flex; align-items: center; gap: 8px;
}
.section-title .step-num {
  width: 24px; height: 24px; background: var(--accent-dim);
  border: 1px solid var(--accent); border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 12px; color: var(--accent); flex-shrink: 0;
}

.error-box {
  background: rgba(248,81,73,0.1); border: 1px solid var(--red);
  border-radius: 6px; padding: 12px 16px; color: var(--red);
  font-size: 13px; margin-bottom: 16px;
}
.success-box {
  background: rgba(63,185,80,0.1); border: 1px solid var(--green);
  border-radius: 6px; padding: 12px 16px; color: var(--green);
  font-size: 13px; margin-bottom: 16px;
}
</style>
