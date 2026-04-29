import React, { useState, useEffect, useRef } from 'react';
import { api } from './api.js';

// ---------------------------------------------------------------------------
// Mock demo rows (for manual mode)
// ---------------------------------------------------------------------------
const MOCK_ROWS = [
  {
    id: 1,
    rut: '15.234.567-K',
    nombre: 'Juan Pérez',
    diagnostico: 'Hipertensión',
    notas: 'El paciente Juan Pérez con RUT 15.234.567-K acude a control',
  },
  {
    id: 2,
    rut: '10.987.654-3',
    nombre: 'María Silva',
    diagnostico: 'Diabetes',
    notas: 'Sra. María (10.987.654-3) presenta glicemia elevada',
  },
  {
    id: 3,
    rut: '20.111.222-5',
    nombre: 'Carlos Rojas',
    diagnostico: 'Asma',
    notas: 'Carlos Rojas, ficha 20.111.222-5, requiere nebulización',
  },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const RISK_COLORS = {
  low: 'bg-green-100 text-green-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-red-100 text-red-800',
};

const FRAMEWORK_LABELS = {
  minsal: 'MINSAL Chile',
  hipaa: 'HIPAA Safe Harbor',
  iso25237: 'ISO 25237',
};

function parseClientCsv(text) {
  const lines = text.split('\n').filter((l) => l.trim());
  if (lines.length === 0) return { headers: [], rows: [] };
  const headers = lines[0].split(',').map((h) => h.trim().replace(/^"|"$/g, ''));
  const rows = lines.slice(1).map((line) => {
    // Simple CSV split (handles basic quoted fields)
    const cells = [];
    let inQuote = false;
    let cell = '';
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (ch === '"') {
        inQuote = !inQuote;
      } else if (ch === ',' && !inQuote) {
        cells.push(cell.trim());
        cell = '';
      } else {
        cell += ch;
      }
    }
    cells.push(cell.trim());
    const obj = {};
    headers.forEach((h, idx) => {
      obj[h] = cells[idx] ?? '';
    });
    return obj;
  });
  return { headers, rows };
}

function tokenizeAnonymized(text) {
  if (!text) return [{ type: 'text', value: '' }];
  const parts = [];
  const re = /(<[A-Z_]+>|\[[A-Z0-9_]+_[A-Za-z0-9_-]+\])/g;
  let last = 0;
  let match;
  while ((match = re.exec(text)) !== null) {
    if (match.index > last) parts.push({ type: 'text', value: text.slice(last, match.index) });
    parts.push({ type: 'token', value: match[0] });
    last = match.index + match[0].length;
  }
  if (last < text.length) parts.push({ type: 'text', value: text.slice(last) });
  return parts;
}

function AnonymizedCell({ text }) {
  const parts = tokenizeAnonymized(text);
  return (
    <span>
      {parts.map((p, i) =>
        p.type === 'token' ? (
          <span key={i} className="inline-block bg-blue-100 text-blue-800 text-xs font-mono px-1 rounded mx-0.5">
            {p.value}
          </span>
        ) : (
          <span key={i}>{p.value}</span>
        )
      )}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Tab components
// ---------------------------------------------------------------------------

function TabIngesta({ inputMode, setInputMode, csvFile, setCsvFile, csvPreview, setCsvPreview }) {
  const fileInputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFile = (file) => {
    if (!file || !file.name.endsWith('.csv')) return;
    setCsvFile(file);
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target.result;
      const parsed = parseClientCsv(text);
      setCsvPreview(parsed);
    };
    reader.readAsText(file, 'utf-8');
  };

  return (
    <div className="space-y-6">
      <div className="flex gap-3">
        {['manual', 'csv'].map((mode) => (
          <button
            key={mode}
            onClick={() => setInputMode(mode)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              inputMode === mode
                ? 'bg-blue-900 text-white'
                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            {mode === 'manual' ? 'Manual (demo)' : 'Subir CSV'}
          </button>
        ))}
      </div>

      {inputMode === 'manual' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="font-semibold text-gray-800">Datos de demostración</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  {['RUT', 'Nombre', 'Diagnóstico', 'Notas'].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {MOCK_ROWS.map((row) => (
                  <tr key={row.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-xs text-red-600">{row.rut}</td>
                    <td className="px-4 py-3">{row.nombre}</td>
                    <td className="px-4 py-3">{row.diagnostico}</td>
                    <td className="px-4 py-3 text-gray-600 max-w-xs truncate">{row.notas}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {inputMode === 'csv' && (
        <div className="space-y-4">
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files[0]); }}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
              dragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              className="hidden"
              onChange={(e) => handleFile(e.target.files[0])}
            />
            <div className="text-4xl mb-3">📂</div>
            <p className="text-gray-600 font-medium">Arrastra tu CSV aquí o haz clic para seleccionar</p>
            <p className="text-gray-400 text-sm mt-1">Solo archivos .csv — máximo 10 MB</p>
          </div>

          {csvFile && (
            <div className="flex items-center gap-3 bg-green-50 border border-green-200 rounded-lg px-4 py-3">
              <span className="text-green-600 text-xl">✓</span>
              <div>
                <p className="font-medium text-green-800">{csvFile.name}</p>
                <p className="text-green-600 text-sm">{(csvFile.size / 1024).toFixed(1)} KB</p>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); setCsvFile(null); setCsvPreview(null); }}
                className="ml-auto text-gray-400 hover:text-red-500"
              >
                ✕
              </button>
            </div>
          )}

          {csvPreview && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="font-semibold text-gray-800">
                  Vista previa — {csvPreview.rows.length} filas detectadas (mostrando las primeras 5)
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      {csvPreview.headers.map((h) => (
                        <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {csvPreview.rows.slice(0, 5).map((row, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        {csvPreview.headers.map((h) => (
                          <td key={h} className="px-4 py-3 max-w-xs truncate text-gray-700">
                            {row[h]}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function TabPolicies({ policy, setPolicy, language, setLanguage, inputMode, csvPreview, columnMappings, setColumnMappings }) {
  const frameworks = [
    { id: 'minsal', label: 'MINSAL Chile', desc: 'Ley 19.628 — Entidades chilenas: RUT, FONASA, teléfonos' },
    { id: 'hipaa', label: 'HIPAA Safe Harbor', desc: '18 categorías PHI — Nombres, SSN, emails, IPs, etc.' },
    { id: 'iso25237', label: 'ISO 25237', desc: 'Pseudonimización HMAC-SHA256 — tokens reversibles [TIPO_xxx]' },
  ];

  const handleMappingChange = (col, value) => {
    setColumnMappings((prev) => ({ ...prev, [col]: value }));
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="font-semibold text-gray-800 mb-3">Marco de compliance</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {frameworks.map((fw) => (
            <button
              key={fw.id}
              onClick={() => setPolicy(fw.id)}
              className={`text-left p-4 rounded-xl border-2 transition-all ${
                policy === fw.id
                  ? 'border-blue-600 bg-blue-50 shadow-md'
                  : 'border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50'
              }`}
            >
              <div className="font-semibold text-gray-800">{fw.label}</div>
              <div className="text-sm text-gray-500 mt-1">{fw.desc}</div>
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block font-semibold text-gray-800 mb-2">Idioma del texto</label>
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="w-40 px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-700"
        >
          <option value="es">Español (es)</option>
          <option value="en">English (en)</option>
        </select>
      </div>

      {inputMode === 'csv' && csvPreview && csvPreview.headers.length > 0 && (
        <div>
          <h3 className="font-semibold text-gray-800 mb-3">Mapeo de columnas</h3>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Columna</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Tratamiento</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {csvPreview.headers.map((col) => (
                  <tr key={col}>
                    <td className="px-4 py-3 font-mono text-xs">{col}</td>
                    <td className="px-4 py-3">
                      <select
                        value={columnMappings[col] || 'text'}
                        onChange={(e) => handleMappingChange(col, e.target.value)}
                        className="px-2 py-1 border border-gray-300 rounded text-sm bg-white"
                      >
                        <option value="text">Texto libre (NLP)</option>
                        <option value="skip">Omitir</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function TabPreview({ inputMode, policy, language, csvFile, csvPreview, columnMappings }) {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [csvResult, setCsvResult] = useState(null);
  const [error, setError] = useState(null);
  const [rowLoading, setRowLoading] = useState({});

  const callApiForRow = async (row) => {
    const text = row.notas || '';
    if (policy === 'minsal') return api.anonymizeMinsal(text, language);
    if (policy === 'hipaa') return api.anonymizeHipaa(text, language);
    if (policy === 'iso25237') return api.pseudonymize(text, language);
    return api.anonymizeMinsal(text, language);
  };

  const runManual = async () => {
    setLoading(true);
    setError(null);
    setResults(null);
    const newResults = [];
    for (let i = 0; i < MOCK_ROWS.length; i++) {
      setRowLoading((prev) => ({ ...prev, [i]: true }));
      try {
        const res = await callApiForRow(MOCK_ROWS[i]);
        newResults.push({ ...MOCK_ROWS[i], anonymizedNotas: res.text ?? res.pseudonymized_text ?? res.text, risk_score: res.risk_score, risk_level: res.risk_level });
      } catch (e) {
        newResults.push({ ...MOCK_ROWS[i], anonymizedNotas: '[Error]', error: e.message });
      }
      setRowLoading((prev) => ({ ...prev, [i]: false }));
    }
    setResults(newResults);
    setLoading(false);
  };

  const runCsv = async () => {
    if (!csvFile) return;
    setLoading(true);
    setError(null);
    setCsvResult(null);
    const textColumns = csvPreview
      ? csvPreview.headers.filter((h) => (columnMappings[h] || 'text') === 'text')
      : null;
    const config = { framework: policy, language, text_columns: textColumns };
    try {
      const res = await api.processCsv(csvFile, config);
      setCsvResult(res);
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  };

  const handleDownload = async () => {
    if (!csvFile) return;
    const textColumns = csvPreview
      ? csvPreview.headers.filter((h) => (columnMappings[h] || 'text') === 'text')
      : null;
    const config = { framework: policy, language, text_columns: textColumns };
    try {
      const blob = await api.downloadCsv(csvFile, config);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `anonymized_${csvFile.name}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-red-700 text-sm">
          ⚠️ {error}
        </div>
      )}

      <div className="flex gap-3 flex-wrap">
        <button
          onClick={inputMode === 'manual' ? runManual : runCsv}
          disabled={loading || (inputMode === 'csv' && !csvFile)}
          className="px-6 py-2 bg-blue-900 text-white rounded-lg font-medium hover:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {loading && <span className="animate-spin">⏳</span>}
          Ejecutar Motor ({FRAMEWORK_LABELS[policy] || policy})
        </button>
        {inputMode === 'csv' && csvResult && (
          <button
            onClick={handleDownload}
            className="px-6 py-2 bg-green-700 text-white rounded-lg font-medium hover:bg-green-600 flex items-center gap-2"
          >
            ⬇ Exportar CSV
          </button>
        )}
      </div>

      {/* Manual mode results */}
      {inputMode === 'manual' && results && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  {['RUT', 'Nombre', 'Diagnóstico', 'Notas Anonimizadas', 'Riesgo'].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {results.map((row, i) => (
                  <tr key={row.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-xs text-blue-700">{row.rut}</td>
                    <td className="px-4 py-3">{row.nombre}</td>
                    <td className="px-4 py-3">{row.diagnostico}</td>
                    <td className="px-4 py-3">
                      {rowLoading[i] ? (
                        <span className="text-gray-400 animate-pulse">Procesando…</span>
                      ) : (
                        <AnonymizedCell text={row.anonymizedNotas} />
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {row.risk_level && (
                        <span className={`text-xs font-medium px-2 py-1 rounded-full ${RISK_COLORS[row.risk_level] || 'bg-gray-100 text-gray-600'}`}>
                          {row.risk_level}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* CSV mode results */}
      {inputMode === 'csv' && csvResult && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Filas procesadas', value: csvResult.total_rows },
              { label: 'Framework', value: csvResult.framework },
              { label: 'Riesgo promedio', value: `${(csvResult.overall_risk_score * 100).toFixed(1)}%` },
              {
                label: 'Nivel de riesgo',
                value: (
                  <span className={`text-xs font-medium px-2 py-1 rounded-full ${RISK_COLORS[csvResult.overall_risk_level] || 'bg-gray-100 text-gray-600'}`}>
                    {csvResult.overall_risk_level}
                  </span>
                ),
              },
            ].map((stat) => (
              <div key={stat.label} className="bg-white rounded-xl border border-gray-200 p-4 text-center">
                <div className="text-2xl font-bold text-blue-900">{stat.value}</div>
                <div className="text-xs text-gray-500 mt-1">{stat.label}</div>
              </div>
            ))}
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">#</th>
                    {csvResult.rows[0] &&
                      Object.keys(csvResult.rows[0].anonymized).map((col) => (
                        <th key={col} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
                          {col}
                        </th>
                      ))}
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Riesgo</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {csvResult.rows.map((row) => (
                    <tr key={row.row_index} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-gray-400 text-xs">{row.row_index + 1}</td>
                      {Object.values(row.anonymized).map((val, ci) => (
                        <td key={ci} className="px-4 py-3 max-w-xs">
                          <AnonymizedCell text={String(val)} />
                        </td>
                      ))}
                      <td className="px-4 py-3">
                        <span className={`text-xs font-medium px-2 py-1 rounded-full ${RISK_COLORS[row.risk_score > 0.6 ? 'high' : row.risk_score > 0.25 ? 'medium' : 'low']}`}>
                          {((row.risk_score || 0) * 100).toFixed(0)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function TabAudit() {
  const [entries, setEntries] = useState([]);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = async (fw) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAuditLog(50, fw || null);
      setEntries(data.entries || []);
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  };

  useEffect(() => {
    load(filter);
  }, [filter]);

  const totalOps = entries.length;
  const avgRisk = entries.length
    ? (entries.reduce((s, e) => s + (e.risk_score || 0), 0) / entries.length).toFixed(3)
    : '—';
  const frameworkCounts = entries.reduce((acc, e) => {
    acc[e.framework] = (acc[e.framework] || 0) + 1;
    return acc;
  }, {});
  const topFw = Object.entries(frameworkCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || '—';

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-red-700 text-sm">⚠️ {error}</div>
      )}

      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Total operaciones', value: totalOps },
          { label: 'Riesgo promedio', value: avgRisk },
          { label: 'Framework más usado', value: topFw },
        ].map((stat) => (
          <div key={stat.label} className="bg-white rounded-xl border border-gray-200 p-4 text-center">
            <div className="text-2xl font-bold text-blue-900">{stat.value}</div>
            <div className="text-xs text-gray-500 mt-1">{stat.label}</div>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-3">
        <label className="text-sm font-medium text-gray-700">Filtrar por framework:</label>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm bg-white"
        >
          <option value="">Todos</option>
          <option value="minsal">MINSAL</option>
          <option value="hipaa-safe-harbor">HIPAA Safe Harbor</option>
          <option value="hipaa-expert-determination">HIPAA Expert Det.</option>
          <option value="iso-25237">ISO 25237</option>
          <option value="hipaa">HIPAA (CSV)</option>
          <option value="iso25237">ISO 25237 (CSV)</option>
          <option value="CSV_PROCESS">CSV Process</option>
        </select>
        <button
          onClick={() => load(filter)}
          className="px-3 py-1.5 bg-blue-900 text-white rounded-lg text-sm hover:bg-blue-800"
        >
          {loading ? '⏳' : '↻'} Actualizar
        </button>
      </div>

      {entries.length === 0 && !loading && (
        <div className="text-gray-400 text-center py-10">Sin entradas de auditoría. Ejecuta alguna operación primero.</div>
      )}

      {entries.length > 0 && (
        <>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    {['Timestamp', 'Framework', 'Operación', 'Entidades', 'Riesgo', 'Long. entrada'].map((h) => (
                      <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {entries.map((entry, i) => (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">
                        {new Date(entry.timestamp).toLocaleString('es-CL')}
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-xs bg-blue-100 text-blue-800 font-medium px-2 py-0.5 rounded-full">
                          {entry.framework}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs">{entry.operation}</td>
                      <td className="px-4 py-3 text-xs text-gray-600">
                        {(entry.entities_found || []).slice(0, 3).join(', ')}
                        {(entry.entities_found || []).length > 3 ? '…' : ''}
                      </td>
                      <td className="px-4 py-3">
                        {entry.risk_score != null && (
                          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${RISK_COLORS[entry.risk_score > 0.6 ? 'high' : entry.risk_score > 0.25 ? 'medium' : 'low']}`}>
                            {(entry.risk_score * 100).toFixed(0)}%
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-500">{entry.input_length} chars</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Timeline */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-800 mb-4">Línea de tiempo</h3>
            <div className="space-y-3">
              {entries.slice(-8).reverse().map((entry, i) => (
                <div key={i} className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-blue-500 mt-2 flex-shrink-0" />
                  <div>
                    <span className="text-xs text-gray-500">{new Date(entry.timestamp).toLocaleString('es-CL')} — </span>
                    <span className="text-sm font-medium text-gray-800">{entry.operation}</span>
                    <span className="text-xs text-gray-500"> · {entry.framework}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main App
// ---------------------------------------------------------------------------

const TABS = [
  { id: 'ingesta', label: '① Ingesta de Datos' },
  { id: 'politicas', label: '② Políticas & NLP' },
  { id: 'preview', label: '③ Previsualización' },
  { id: 'auditoria', label: '④ Reportes & Auditoría' },
];

export default function App() {
  const [activeTab, setActiveTab] = useState('ingesta');
  const [inputMode, setInputMode] = useState('manual');
  const [csvFile, setCsvFile] = useState(null);
  const [csvPreview, setCsvPreview] = useState(null);
  const [policy, setPolicy] = useState('minsal');
  const [language, setLanguage] = useState('es');
  const [columnMappings, setColumnMappings] = useState({});
  const [apiConnected, setApiConnected] = useState(null);

  useEffect(() => {
    api.healthCheck()
      .then(() => setApiConnected(true))
      .catch(() => setApiConnected(false));
  }, []);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-blue-900 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold tracking-wide">PRISMA IA</h1>
            <p className="text-blue-300 text-xs mt-0.5">Data Masking Platform — Compliance MINSAL · HIPAA · ISO 25237</p>
          </div>
          <div>
            {apiConnected === false && (
              <span className="bg-red-500 text-white text-xs font-semibold px-3 py-1 rounded-full animate-pulse">
                ⚡ API Desconectada
              </span>
            )}
            {apiConnected === true && (
              <span className="bg-green-500 text-white text-xs font-semibold px-3 py-1 rounded-full">
                ✓ API Conectada
              </span>
            )}
          </div>
        </div>
        {/* Tabs */}
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex gap-1 border-b border-blue-800">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-3 text-sm font-medium transition-colors border-b-2 -mb-px ${
                  activeTab === tab.id
                    ? 'border-white text-white'
                    : 'border-transparent text-blue-300 hover:text-white'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {activeTab === 'ingesta' && (
          <TabIngesta
            inputMode={inputMode}
            setInputMode={setInputMode}
            csvFile={csvFile}
            setCsvFile={setCsvFile}
            csvPreview={csvPreview}
            setCsvPreview={setCsvPreview}
          />
        )}
        {activeTab === 'politicas' && (
          <TabPolicies
            policy={policy}
            setPolicy={setPolicy}
            language={language}
            setLanguage={setLanguage}
            inputMode={inputMode}
            csvPreview={csvPreview}
            columnMappings={columnMappings}
            setColumnMappings={setColumnMappings}
          />
        )}
        {activeTab === 'preview' && (
          <TabPreview
            inputMode={inputMode}
            policy={policy}
            language={language}
            csvFile={csvFile}
            csvPreview={csvPreview}
            columnMappings={columnMappings}
          />
        )}
        {activeTab === 'auditoria' && <TabAudit />}
      </main>
    </div>
  );
}
