const BASE_URL = import.meta.env.VITE_API_URL || '/api';

export const api = {
  async anonymizeMinsal(text, language = 'es') {
    const res = await fetch(`${BASE_URL}/compliance/minsal`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, language }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async anonymizeHipaa(text, language = 'es') {
    const res = await fetch(`${BASE_URL}/compliance/hipaa/safe-harbor`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, language }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async pseudonymize(text, language = 'es') {
    const res = await fetch(`${BASE_URL}/compliance/iso25237/pseudonymize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, language }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async expertDetermination(text, language = 'es') {
    const res = await fetch(`${BASE_URL}/compliance/hipaa/expert-determination`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, language }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async processCsv(file, config) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('config', JSON.stringify(config));
    const res = await fetch(`${BASE_URL}/csv/process`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async downloadCsv(file, config) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('config', JSON.stringify(config));
    const res = await fetch(`${BASE_URL}/csv/process/download`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error(await res.text());
    return res.blob();
  },

  async getAuditLog(limit = 50, framework = null) {
    const params = new URLSearchParams({ limit });
    if (framework) params.append('framework', framework);
    const res = await fetch(`${BASE_URL}/compliance/audit-log?${params}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getFrameworks() {
    const res = await fetch(`${BASE_URL}/compliance/frameworks`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async healthCheck() {
    const base = import.meta.env.VITE_API_URL || '';
    const res = await fetch(`${base}/`);
    if (!res.ok) throw new Error('API unavailable');
    return res.json();
  },
};
