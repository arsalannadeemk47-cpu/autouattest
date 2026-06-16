const fs = require('fs');
const path = require('path');

class LicenseReporter {
  constructor() {
    this.results = [];
    this.startTime = Date.now();
  }

  onBegin(_config, suite) {
    this.startTime = Date.now();
    console.log(`\n🧪 Running ${suite.allTests().length} license validator tests...\n`);
  }

  onTestEnd(test, result) {
    const title = test.title;

    const codeMatch = title.match(/License\s+([A-Z0-9-]+)\s+-/i);
    const licenseCode = codeMatch ? codeMatch[1] : 'Unknown';

    const stdout = result.stdout
      .map(s => (typeof s === 'string' ? s : s.toString()))
      .join('\n');

    const expectedMatch = stdout.match(/Expected permits:\s*(.+)/);
    const visibleMatch  = stdout.match(/Visible permits:\s*(.+)/);
    const missingMatch  = stdout.match(/❌ Missing permits:\s*(.+)/);
    const unexpectedMatch = stdout.match(/❌ Unexpected permits:\s*(.+)/);
    const numberMatch   = stdout.match(/License\s+[A-Z0-9-]+\s+\((\d+)\)/);

    const expectedPermits  = expectedMatch  ? expectedMatch[1].split(',').map(s => s.trim()).filter(Boolean)  : [];
    const visiblePermits   = visibleMatch   ? visibleMatch[1].split(',').map(s => s.trim()).filter(Boolean)   : [];
    const missingPermits   = missingMatch   ? missingMatch[1].split(',').map(s => s.trim()).filter(Boolean)   : [];
    const unexpectedPermits = unexpectedMatch ? unexpectedMatch[1].split(',').map(s => s.trim()).filter(Boolean) : [];
    const licenseNumber    = numberMatch    ? numberMatch[1] : '';

    // Read screenshot attachments and encode as base64
    const screenshots = [];
    for (const attachment of result.attachments || []) {
      if (attachment.name === 'screenshot' && attachment.path) {
        try {
          const imgBuffer = fs.readFileSync(attachment.path);
          const base64 = imgBuffer.toString('base64');
          screenshots.push(`data:image/png;base64,${base64}`);
        } catch (e) {
          // Screenshot file missing — skip
        }
      }
    }

    let failureReason = '';
    if (result.status === 'timedOut') {
      failureReason = 'Test timed out — could not reach Application Template page';
    } else if (result.status === 'failed') {
      if (missingPermits.length > 0 && unexpectedPermits.length > 0) {
        failureReason = 'Missing and unexpected permit types found';
      } else if (missingPermits.length > 0) {
        failureReason = 'Missing permit types';
      } else if (unexpectedPermits.length > 0) {
        failureReason = 'Unexpected permit types found';
      } else {
        const errMsg = (result.errors[0] && result.errors[0].message) || '';
        failureReason = errMsg.split('\n')[0].substring(0, 120) || 'Test failed';
      }
    }

    this.results.push({
      title,
      licenseCode,
      licenseNumber,
      status: result.status,
      failureReason,
      missingPermits,
      unexpectedPermits,
      expectedPermits,
      visiblePermits,
      duration: result.duration,
      screenshots,
    });
  }

  onEnd(_result) {
    const totalDuration = ((Date.now() - this.startTime) / 1000).toFixed(1);
    const passed   = this.results.filter(r => r.status === 'passed').length;
    const failed   = this.results.filter(r => r.status === 'failed').length;
    const timedOut = this.results.filter(r => r.status === 'timedOut').length;
    const total    = this.results.length;

    const html = this.buildHTML(passed, failed, timedOut, total, totalDuration);

    const outDir  = path.join(process.cwd(), 'license-report');
    fs.mkdirSync(outDir, { recursive: true });
    const outPath = path.join(outDir, 'index.html');
    fs.writeFileSync(outPath, html, 'utf-8');

    console.log(`\n📊 License report saved to: ${outPath}`);
  }

  statusPill(status, failureReason) {
    if (status === 'passed') return `<span class="pill pill-pass">✓ Passed</span>`;
    if (status === 'timedOut') return `<span class="pill pill-timeout">⏱ Timed Out</span>`;
    if (failureReason.includes('Missing and unexpected')) return `<span class="pill pill-fail">✗ Missing + Extra</span>`;
    if (failureReason.includes('Missing')) return `<span class="pill pill-missing">✗ Missing Permits</span>`;
    if (failureReason.includes('Unexpected') || failureReason.includes('unexpected')) return `<span class="pill pill-extra">✗ Extra Permits</span>`;
    return `<span class="pill pill-fail">✗ Failed</span>`;
  }

  buildHTML(passed, failed, timedOut, total, duration) {
    const passRate = total > 0 ? Math.round((passed / total) * 100) : 0;
    const now = new Date().toLocaleString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });

    const rows = this.results.map((r, i) => {
      const expectedList = r.expectedPermits.length
        ? r.expectedPermits.map(p => `<span class="tag tag-expected">${p}</span>`).join(' ')
        : '<span class="muted">—</span>';

      const visibleList = r.visiblePermits.length
        ? r.visiblePermits.map(p => {
            const isMissing = r.missingPermits.some(m => m.toLowerCase() === p.toLowerCase());
            return `<span class="tag ${isMissing ? 'tag-missing' : 'tag-ok'}">${p}</span>`;
          }).join(' ')
        : '<span class="muted">—</span>';

      const missingList = r.missingPermits.length
        ? r.missingPermits.map(p => `<span class="tag tag-missing">${p}</span>`).join(' ')
        : '<span class="muted">None</span>';

      const extraList = r.unexpectedPermits.length
        ? r.unexpectedPermits.map(p => `<span class="tag tag-extra">${p}</span>`).join(' ')
        : '<span class="muted">None</span>';

      const detailId  = `detail-${i}`;
      const showDetail = r.status !== 'passed';

      const screenshotHtml = (r.screenshots && r.screenshots.length > 0)
        ? r.screenshots.map(src => `
            <div class="detail-block detail-block-screenshot">
              <div class="detail-label">Screenshot</div>
              <img src="${src}" class="screenshot-img" onclick="expandImg(this)" />
            </div>`).join('')
        : '';

      return `
          <tr class="row-main ${r.status === 'passed' ? 'row-pass' : 'row-fail'}"
            onclick="toggleDetail('${detailId}')" style="cursor:pointer">
          <td class="td-code"><span class="code-badge">${r.licenseCode}</span></td>
          <td class="td-num">${r.licenseNumber || '—'}</td>
          <td>${this.statusPill(r.status, r.failureReason)}</td>
          <td class="td-permits">${expectedList}</td>
          <td class="td-reason">${r.status === 'passed' ? '<span class="muted">—</span>' : r.failureReason}</td>
          <td class="td-dur">${(r.duration / 1000).toFixed(1)}s</td>
          <td class="td-toggle">${showDetail ? '<span class="chevron">▾</span>' : ''}</td>
        </tr>
        <tr id="${detailId}" class="row-detail" style="display:none">
          <td colspan="7">
            <div class="detail-grid">
              <div class="detail-block">
                <div class="detail-label">Expected Permits</div>
                <div>${expectedList}</div>
              </div>
              <div class="detail-block">
                <div class="detail-label">Found on Page</div>
                <div>${visibleList}</div>
              </div>
              <div class="detail-block">
                <div class="detail-label">Missing</div>
                <div>${missingList}</div>
              </div>
              <div class="detail-block">
                <div class="detail-label">Unexpected</div>
                <div>${extraList}</div>
              </div>
              ${screenshotHtml}
            </div>
          </td>
        </tr>`;
    }).join('');

    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>License Validator Report</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #0d1117; --surface: #161b22; --border: #30363d;
    --text: #e6edf3; --muted: #6e7681;
    --pass: #2ea043; --pass-bg: #0d2c17;
    --fail: #da3633; --fail-bg: #2c0d0d;
    --warn: #d29922; --warn-bg: #2c1f0d;
    --extra: #8957e5; --extra-bg: #1e1038;
  }
  body { font-family: 'Inter', system-ui, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; padding: 2rem; }
  header { margin-bottom: 2rem; }
  .eyebrow { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted); margin-bottom: 0.4rem; }
  h1 { font-size: 1.6rem; font-weight: 700; margin-bottom: 0.25rem; }
  .run-meta { font-size: 0.8rem; color: var(--muted); font-family: 'JetBrains Mono', monospace; }
  .summary-bar { display: grid; grid-template-columns: repeat(4, 1fr) 2fr; gap: 1rem; margin-bottom: 2rem; }
  .stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1rem 1.2rem; }
  .stat-label { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); margin-bottom: 0.4rem; }
  .stat-value { font-size: 2rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; line-height: 1; }
  .stat-value.green { color: var(--pass); } .stat-value.red { color: var(--fail); } .stat-value.gray { color: var(--muted); } .stat-value.white { color: var(--text); }
  .progress-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1rem 1.2rem; display: flex; flex-direction: column; justify-content: space-between; }
  .progress-bar-track { background: var(--border); border-radius: 4px; height: 8px; margin-top: 0.6rem; overflow: hidden; }
  .progress-bar-fill { height: 100%; border-radius: 4px; background: var(--pass); }
  .progress-label { font-size: 2rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: var(--pass); }
  .table-wrap { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
  table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
  thead th { background: #1c2128; color: var(--muted); font-size: 0.68rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid var(--border); }
  tbody tr.row-main:hover { background: #1c2128; }
  tbody tr.row-main td { padding: 0.75rem 1rem; border-bottom: 1px solid var(--border); vertical-align: middle; }
  tbody tr.row-detail td { padding: 0; border-bottom: 1px solid var(--border); background: #0d1117; }
  .detail-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px; background: var(--border); }
  .detail-block { background: #0d1117; padding: 1rem; }
  .detail-label { font-size: 0.65rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); margin-bottom: 0.5rem; }
  .code-badge { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; font-weight: 600; background: #1f2937; border: 1px solid var(--border); border-radius: 4px; padding: 0.2rem 0.5rem; color: #79c0ff; }
  .td-num { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: var(--muted); }
  .td-dur { font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: var(--muted); text-align: right; }
  .td-toggle { text-align: center; color: var(--muted); width: 2rem; }
  .chevron { font-size: 1rem; }
  .pill { display: inline-block; font-size: 0.72rem; font-weight: 600; padding: 0.2rem 0.6rem; border-radius: 20px; white-space: nowrap; }
  .pill-pass    { background: var(--pass-bg);  color: #56d364; border: 1px solid #2ea043; }
  .pill-fail    { background: var(--fail-bg);  color: #ff7b72; border: 1px solid #da3633; }
  .pill-missing { background: var(--warn-bg);  color: #e3b341; border: 1px solid #d29922; }
  .pill-extra   { background: var(--extra-bg); color: #d2a8ff; border: 1px solid #8957e5; }
  .pill-timeout { background: #161b22; color: var(--muted); border: 1px solid var(--border); }
  .tag { display: inline-block; font-size: 0.72rem; padding: 0.15rem 0.45rem; border-radius: 4px; margin: 0.1rem; font-weight: 500; }
  .tag-expected { background: #1f2937; color: #79c0ff; border: 1px solid #30363d; }
  .tag-ok       { background: var(--pass-bg); color: #56d364; border: 1px solid #2ea04360; }
  .tag-missing  { background: var(--warn-bg); color: #e3b341; border: 1px solid #d2992260; }
  .tag-extra    { background: var(--extra-bg); color: #d2a8ff; border: 1px solid #8957e560; }
  .muted { color: var(--muted); font-size: 0.8rem; }
  .td-reason { font-size: 0.78rem; color: var(--muted); max-width: 220px; }
  .td-permits { max-width: 260px; }
footer { margin-top: 2rem; text-align: center; font-size: 0.72rem; color: var(--muted); font-family: 'JetBrains Mono', monospace; }
  .detail-block-screenshot { grid-column: 1 / -1; }
  .screenshot-img { max-width: 100%; border-radius: 6px; border: 1px solid var(--border); cursor: zoom-in; margin-top: 0.5rem; }
  .lightbox { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:1000; justify-content:center; align-items:center; }
  .lightbox.active { display:flex; }
  .lightbox img { max-width:90vw; max-height:90vh; border-radius:8px; box-shadow:0 0 60px rgba(0,0,0,0.8); }
</style>
</head>
<body>
<header>
  <div class="eyebrow">LA City Permitting · UAT</div>
  <h1>License Validator Report</h1>
  <div class="run-meta">Generated ${now} · ${duration}s total runtime</div>
</header>
<div class="summary-bar">
  <div class="stat-card"><div class="stat-label">Total Tests</div><div class="stat-value white">${total}</div></div>
  <div class="stat-card"><div class="stat-label">Passed</div><div class="stat-value green">${passed}</div></div>
  <div class="stat-card"><div class="stat-label">Failed</div><div class="stat-value red">${failed}</div></div>
  <div class="stat-card"><div class="stat-label">Timed Out</div><div class="stat-value gray">${timedOut}</div></div>
  <div class="progress-card">
    <div><div class="stat-label">Pass Rate</div><div class="progress-label">${passRate}%</div></div>
    <div class="progress-bar-track"><div class="progress-bar-fill" style="width:${passRate}%"></div></div>
  </div>
</div>
<div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th>License Code</th><th>License #</th><th>Result</th>
        <th>Expected Permits</th><th>Failure Reason</th>
        <th style="text-align:right">Duration</th><th></th>
      </tr>
    </thead>
    <tbody>${rows}</tbody>
  </table>
</div>
<footer>lacps--uat.sandbox.my.site.com · Playwright Test Automation</footer>
<div id="lightbox" class="lightbox" onclick="this.classList.remove('active')">
  <img id="lightbox-img" src="" />
</div>
<script>
  function toggleDetail(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.style.display = (el.style.display === 'none' || el.style.display === '') ? 'table-row' : 'none';
  }
  function expandImg(img) {
    event.stopPropagation();
    document.getElementById('lightbox-img').src = img.src;
    document.getElementById('lightbox').classList.add('active');
  }
</script>
</body>
</html>`;
  }
}

module.exports = LicenseReporter;