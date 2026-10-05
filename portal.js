'use strict';

const SUPABASE_URL = "https://arsogtofweecxsvxuwxf.supabase.co";
const SUPABASE_KEY = "sb_publishable__VDKOy7W68wCvlu1n-lOig_oBsUV7rk";
const SESSION_KEY = 'rumbo_session_v1';

function qs(selector) { return document.querySelector(selector); }
function qsa(selector) { return Array.from(document.querySelectorAll(selector)); }

function showStatus(message, kind = 'info') {
  const node = qs('[data-status]');
  if (!node) return;
  node.textContent = message;
  node.dataset.kind = kind;
}

function storedSession() {
  try { return JSON.parse(sessionStorage.getItem(SESSION_KEY) || 'null'); }
  catch { return null; }
}

function saveSession(session) {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

function clearSession() {
  sessionStorage.removeItem(SESSION_KEY);
}

function authHeaders(session) {
  return {
    apikey: SUPABASE_KEY,
    Authorization: `Bearer ${session.access_token}`,
    'Content-Type': 'application/json'
  };
}

async function authRequest(path, options = {}) {
  const response = await fetch(`${SUPABASE_URL}/auth/v1${path}`, {
    ...options,
    headers: {
      apikey: SUPABASE_KEY,
      'Content-Type': 'application/json',
      ...(options.headers || {})
    }
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.msg || data.message || data.error_description || 'Authentication request failed');
  return data;
}

async function rest(path, { method = 'GET', body, session = storedSession(), prefer } = {}) {
  const headers = {
    apikey: SUPABASE_KEY,
    'Content-Type': 'application/json'
  };
  if (session?.access_token) headers.Authorization = `Bearer ${session.access_token}`;
  if (prefer) headers.Prefer = prefer;
  const response = await fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body)
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(data?.message || data?.hint || `Request failed (${response.status})`);
  return data;
}

async function currentUser(session = storedSession()) {
  if (!session?.access_token) return null;
  try {
    const response = await fetch(`${SUPABASE_URL}/auth/v1/user`, { headers: authHeaders(session) });
    if (response.status === 401) { clearSession(); return null; }
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || 'Unable to read session');
    return data;
  } catch (error) {
    showStatus(error.message, 'error');
    return null;
  }
}

function acceptOAuthHash() {
  if (!location.hash) return false;
  const params = new URLSearchParams(location.hash.slice(1));
  const accessToken = params.get('access_token');
  if (!accessToken) {
    const error = params.get('error_description') || params.get('error');
    if (error) showStatus(error, 'error');
    return false;
  }
  saveSession({
    access_token: accessToken,
    refresh_token: params.get('refresh_token'),
    expires_in: Number(params.get('expires_in') || 0),
    token_type: params.get('token_type') || 'bearer',
    provider_token: null
  });
  history.replaceState(null, '', location.pathname + location.search);
  return true;
}

async function handleLogin(event) {
  event.preventDefault();
  const email = qs('#email').value.trim();
  const password = qs('#password').value;
  showStatus('Authenticating…');
  try {
    const data = await authRequest('/token?grant_type=password', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    saveSession(data);
    showStatus('Authenticated. Redirecting…', 'success');
    location.href = 'dashboard.html';
  } catch (error) {
    showStatus(error.message, 'error');
  }
}

async function handleSignup() {
  const email = qs('#email').value.trim();
  const password = qs('#password').value;
  if (!email || password.length < 8) {
    showStatus('Use a valid email and a password of at least 8 characters.', 'error');
    return;
  }
  showStatus('Creating account…');
  try {
    const redirectTo = new URL('login.html', location.href).href;
    const data = await authRequest(`/signup?redirect_to=${encodeURIComponent(redirectTo)}`, {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    if (data.access_token) {
      saveSession(data);
      showStatus('Account created. Redirecting…', 'success');
      location.href = 'dashboard.html';
    } else {
      showStatus('Account created. Check your email if confirmation is required.', 'success');
    }
  } catch (error) {
    showStatus(error.message, 'error');
  }
}

async function handleLogout() {
  const session = storedSession();
  if (session?.access_token) {
    try {
      await fetch(`${SUPABASE_URL}/auth/v1/logout`, {
        method: 'POST',
        headers: authHeaders(session)
      });
    } catch {}
  }
  clearSession();
  location.href = 'login.html';
}

async function workspaceContext(user, session) {
  const memberships = await rest(
    `workspace_members?select=workspace_id,role&user_id=eq.${encodeURIComponent(user.id)}&limit=1`,
    { session }
  );
  if (!memberships?.length) return null;
  const membership = memberships[0];
  const rows = await rest(
    `workspaces?select=id,name,slug,plan_id&id=eq.${encodeURIComponent(membership.workspace_id)}&limit=1`,
    { session }
  );
  return rows?.length ? { ...rows[0], role: membership.role } : null;
}

function renderRows(target, rows, fields) {
  const node = qs(target);
  if (!node) return;
  node.replaceChildren();
  if (!rows?.length) {
    const empty = document.createElement('p');
    empty.textContent = 'No records yet.';
    node.appendChild(empty);
    return;
  }
  for (const row of rows) {
    const article = document.createElement('article');
    for (const [key, label] of fields) {
      const p = document.createElement('p');
      const strong = document.createElement('strong');
      strong.textContent = label + ': ';
      p.appendChild(strong);
      p.append(document.createTextNode(row[key] === null || row[key] === undefined ? '—' : String(row[key])));
      article.appendChild(p);
    }
    node.appendChild(article);
  }
}

async function loadDashboard() {
  acceptOAuthHash();
  const session = storedSession();
  const user = await currentUser(session);
  if (!user) { location.href = 'login.html'; return; }
  const emailNode = qs('[data-user-email]');
  if (emailNode) emailNode.textContent = user.email || user.id;

  try {
    const workspace = await workspaceContext(user, session);
    if (!workspace) {
      showStatus('Account is valid but no workspace is assigned yet.', 'info');
      return;
    }
    qsa('[data-workspace-name]').forEach(n => { n.textContent = workspace.name; });
    qsa('[data-workspace-plan]').forEach(n => { n.textContent = workspace.plan_id; });
    qsa('[data-workspace-role]').forEach(n => { n.textContent = workspace.role; });

    const wid = encodeURIComponent(workspace.id);
    const [usage, receipts, calls] = await Promise.all([
      rest(`rumbo_usage_events?select=occurred_at,meter,billable_units,amount,currency,request_id&workspace_id=eq.${wid}&order=occurred_at.desc&limit=20`, { session }),
      rest(`rumbo_execution_receipts?select=created_at,request_id,effect_status,receipt_hash&workspace_id=eq.${wid}&order=created_at.desc&limit=20`, { session }),
      rest(`rumbo_mcp_calls?select=started_at,server_name,tool_name,status,latency_ms,request_id&workspace_id=eq.${wid}&order=started_at.desc&limit=20`, { session })
    ]);
    renderRows('#usage-list', usage, [['occurred_at','Time'],['meter','Meter'],['billable_units','Units'],['amount','Amount'],['currency','Currency'],['request_id','Request']]);
    renderRows('#receipt-list', receipts, [['created_at','Time'],['request_id','Request'],['effect_status','Effect'],['receipt_hash','Receipt']]);
    renderRows('#call-list', calls, [['started_at','Time'],['server_name','Server'],['tool_name','Tool'],['status','Status'],['latency_ms','Latency ms'],['request_id','Request']]);
    showStatus('Workspace data loaded.', 'success');
  } catch (error) {
    showStatus(error.message, 'error');
  }
}

async function loadSupport() {
  acceptOAuthHash();
  const session = storedSession();
  const user = await currentUser(session);
  if (!user) { location.href = 'login.html'; return; }
  const workspace = await workspaceContext(user, session);
  if (!workspace) {
    showStatus('No workspace is assigned to this account.', 'error');
    qs('#support-form')?.setAttribute('hidden', 'hidden');
    return;
  }
  qs('[data-workspace-name]').textContent = workspace.name;
  const form = qs('#support-form');
  form?.addEventListener('submit', async (event) => {
    event.preventDefault();
    showStatus('Submitting ticket…');
    try {
      await rest('rumbo_support_tickets', {
        method: 'POST',
        session,
        prefer: 'return=minimal',
        body: {
          workspace_id: workspace.id,
          opened_by: user.id,
          category: qs('#category').value,
          severity: qs('#severity').value,
          subject: qs('#subject').value.trim(),
          description: qs('#description').value.trim()
        }
      });
      form.reset();
      showStatus('Ticket submitted.', 'success');
    } catch (error) {
      showStatus(error.message, 'error');
    }
  });
}

async function loadPartners() {
  try {
    const partners = await rest('rumbo_partner_records?select=name,partner_type,website,verified_at&internal_status=eq.ACTIVE&order=name.asc', { session: null });
    const node = qs('#partner-list');
    node.replaceChildren();
    if (!partners?.length) {
      const p = document.createElement('p');
      p.textContent = 'No verified public partners are listed yet.';
      node.appendChild(p);
      return;
    }
    for (const partner of partners) {
      const article = document.createElement('article');
      const h = document.createElement('h3');
      h.textContent = partner.name;
      const p = document.createElement('p');
      p.textContent = partner.partner_type;
      article.append(h, p);
      if (partner.website) {
        const a = document.createElement('a');
        a.href = partner.website;
        a.rel = 'noopener noreferrer';
        a.textContent = 'Partner website';
        article.appendChild(a);
      }
      node.appendChild(article);
    }
  } catch (error) {
    showStatus(error.message, 'error');
  }
}

function init() {
  const acceptedOAuth = acceptOAuthHash();
  if (document.body.dataset.page === 'login' && acceptedOAuth) {
    location.href = 'dashboard.html';
    return;
  }
  qs('#login-form')?.addEventListener('submit', handleLogin);
  qs('#signup-button')?.addEventListener('click', handleSignup);
  qsa('[data-logout]').forEach(n => n.addEventListener('click', handleLogout));
  if (document.body.dataset.page === 'dashboard') loadDashboard();
  if (document.body.dataset.page === 'support') loadSupport();
  if (document.body.dataset.page === 'partners') loadPartners();
}

init();
