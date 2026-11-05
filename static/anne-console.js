(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const state = { models: [], auth: null, timer: null };
  const setPill = (id, label, kind) => {
    const el = $(id); el.textContent = label; el.className = "pill" + (kind ? " " + kind : "");
  };
  async function getJson(path) {
    const response = await fetch(path, {
      method: "GET", credentials: "same-origin", cache: "no-store",
      headers: { "Accept": "application/json" }
    });
    if (response.status === 401 || response.status === 403) throw new Error("Authentication required. Sign in to Hermes and reload this page.");
    if (!response.ok) throw new Error(path + " returned HTTP " + response.status);
    return response.json();
  }
  function normalizeModel(item) {
    if (typeof item === "string") return { id: item, label: item };
    if (!item || typeof item !== "object") return null;
    const id = String(item.id || item.model || item.name || "").trim();
    if (!id) return null;
    return { id, label: String(item.label || item.name || id) };
  }
  function findGrokRoutes(providerPayload) {
    const providers = Array.isArray(providerPayload) ? providerPayload :
      (Array.isArray(providerPayload && providerPayload.providers) ? providerPayload.providers : []);
    const routes = [];
    providers.forEach((provider) => {
      const providerId = String(provider.id || "").toLowerCase();
      if (providerId !== "x-ai" && providerId !== "xai-oauth") return;
      const models = Array.isArray(provider.models) ? provider.models : [];
      models.map(normalizeModel).filter(Boolean).filter((model) => /grok/i.test(model.id + " " + model.label))
        .forEach((model) => routes.push({
          provider: provider.id,
          providerName: provider.display_name || provider.id,
          hasKey: provider.has_key === true,
          model
        }));
    });
    return routes;
  }
  async function loadGrokRoutes() {
    const payload = await getJson("/api/providers");
    const routes = findGrokRoutes(payload);
    state.models = routes;
    const select = $("grok-model");
    select.replaceChildren();
    if (!routes.length) {
      select.add(new Option("No Grok model exposed by this Hermes profile", ""));
      select.disabled = true;
      $("route-button").disabled = true;
      setPill("grok-pill", "Not available", "warn");
      $("grok-detail").textContent = "No Grok model is currently listed by the active Hermes profile.";
      return;
    }
    routes.forEach((route, index) => {
      const option = new Option(route.model.label + " · " + route.providerName, String(index));
      option.dataset.configured = route.hasKey ? "1" : "0";
      select.add(option);
    });
    const configured = routes.filter((route) => route.hasKey);
    const firstConfigured = routes.findIndex((route) => route.hasKey);
    select.value = String(firstConfigured >= 0 ? firstConfigured : 0);
    const selected = routes[Number(select.value)];
    select.disabled = false;
    $("route-button").disabled = !selected.hasKey;
    if (configured.length) {
      setPill("grok-pill", "Provider configured", "good");
      $("grok-detail").textContent = configured.length + " Grok route(s) are configured in Hermes. Selection is session-scoped.";
    } else {
      setPill("grok-pill", "Credential missing", "warn");
      $("grok-detail").textContent = "Grok models are listed, but no xAI credential is configured for this profile.";
    }
  }
  function onModelChange() {
    const selected = state.models[Number($("grok-model").value)];
    $("route-button").disabled = !selected || !selected.hasKey;
    $("route-error").textContent = "";
  }
  async function refreshHealth() {
    try {
      const [auth, health] = await Promise.all([
        getJson("/api/auth/status"), getJson("/api/health/agent")
      ]);
      state.auth = auth;
      const authenticated = auth.auth_enabled === false || auth.logged_in === true;
      setPill("auth-state", authenticated ? "Authenticated" : "Sign-in required", authenticated ? "good" : "warn");
      if (health.alive === true) {
        $("gateway-state").textContent = "Online";
        $("gateway-detail").textContent = "Hermes gateway reports a live runtime.";
        setPill("gateway-pill", "Online", "good");
      } else if (health.alive === false) {
        $("gateway-state").textContent = "Offline";
        $("gateway-detail").textContent = (health.details && health.details.reason) || "Gateway is not reporting as running.";
        setPill("gateway-pill", "Offline", "bad");
      } else {
        $("gateway-state").textContent = "Unknown";
        $("gateway-detail").textContent = (health.details && health.details.reason) || "No authoritative live heartbeat is available.";
        setPill("gateway-pill", "Unverified", "warn");
      }
      $("checked-at").textContent = new Date().toLocaleTimeString();
    } catch (error) {
      $("gateway-state").textContent = "Unavailable";
      $("gateway-detail").textContent = error.message;
      setPill("gateway-pill", "Check failed", "bad");
      setPill("auth-state", "Unverified", "warn");
    }
  }
  async function getCsrfToken() {
    const response = await fetch("/", { credentials: "same-origin", cache: "no-store" });
    if (!response.ok) throw new Error("Could not obtain the authenticated Hermes page context.");
    const html = await response.text();
    const match = html.match(/csrfToken:("(?:\\.|[^"\\])*")/);
    if (!match) {
      if (state.auth && state.auth.auth_enabled === false) return "";
      throw new Error("Hermes did not provide a CSRF token. Reload after signing in.");
    }
    return JSON.parse(match[1]);
  }
  async function openGrokSession() {
    const route = state.models[Number($("grok-model").value)];
    if (!route || !route.hasKey) return;
    $("route-button").disabled = true;
    $("route-button").textContent = "Creating session…";
    $("route-error").textContent = "";
    try {
      const csrf = await getCsrfToken();
      const headers = { "Content-Type": "application/json", "Accept": "application/json" };
      if (csrf) headers["X-Hermes-CSRF-Token"] = csrf;
      const response = await fetch("/api/session/new", {
        method: "POST", credentials: "same-origin", cache: "no-store", headers,
        body: JSON.stringify({
          model: route.model.id,
          model_provider: route.provider,
          worktree: false
        })
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.error || "Hermes session creation failed (HTTP " + response.status + ").");
      const sessionId = data && data.session && data.session.session_id;
      if (!sessionId) throw new Error("Hermes did not return a session ID.");
      window.location.assign("/session/" + encodeURIComponent(sessionId));
    } catch (error) {
      $("route-error").textContent = error.message;
      $("route-button").disabled = false;
      $("route-button").textContent = "Open new Grok session";
    }
  }
  async function refreshAll() {
    await refreshHealth();
    try { await loadGrokRoutes(); }
    catch (error) {
      setPill("grok-pill", "Check failed", "bad");
      $("grok-detail").textContent = error.message;
      $("route-button").disabled = true;
    }
  }
  $("grok-model").addEventListener("change", onModelChange);
  $("route-button").addEventListener("click", openGrokSession);
  refreshAll();
  state.timer = window.setInterval(refreshAll, 20000);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") refreshAll();
  });
})();