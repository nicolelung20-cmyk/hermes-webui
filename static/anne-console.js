(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const state = { providers: [], routes: [], activeProvider: null, auth: null, timer: null };

  const setPill = (id, label, kind) => {
    const el = $(id);
    el.textContent = label;
    el.className = "pill" + (kind ? " " + kind : "");
  };

  async function getJson(path) {
    const response = await fetch(path, {
      method: "GET", credentials: "same-origin", cache: "no-store",
      headers: { "Accept": "application/json" }
    });
    if (response.status === 401 || response.status === 403) {
      throw new Error("Authentication required. Sign in to Hermes and reload this page.");
    }
    if (!response.ok) throw new Error(path + " returned HTTP " + response.status);
    return response.json();
  }

  async function refreshHealth() {
    try {
      const [auth, health] = await Promise.all([
        getJson("/api/auth/status"),
        getJson("/api/health/agent")
      ]);
      state.auth = auth;
      const authenticated = auth.auth_enabled === false || auth.logged_in === true;
      $("auth-state").textContent = authenticated ? "Authenticated" : "Sign-in required";
      setPill("gateway-pill", authenticated ? "Session verified" : "Sign-in required", authenticated ? "good" : "warn");
      if (health.alive === true) {
        $("gateway-state").textContent = "Online";
        $("gateway-detail").textContent = "Hermes runtime reports a live heartbeat.";
        setPill("gateway-pill", "Online", "good");
      } else if (health.alive === false) {
        $("gateway-state").textContent = "Offline";
        $("gateway-detail").textContent = (health.details && health.details.reason) || "Hermes is not reporting as running.";
        setPill("gateway-pill", "Offline", "bad");
      } else {
        $("gateway-state").textContent = "Unknown";
        $("gateway-detail").textContent = (health.details && health.details.reason) || "No authoritative heartbeat is available.";
        setPill("gateway-pill", "Unverified", "warn");
      }
      $("checked-at").textContent = new Date().toLocaleTimeString();
    } catch (error) {
      $("gateway-state").textContent = "Unavailable";
      $("gateway-detail").textContent = error.message;
      $("auth-state").textContent = "Unverified";
      setPill("gateway-pill", "Check failed", "bad");
    }
  }

  function renderCatalog() {
    const catalog = $("provider-catalog");
    catalog.replaceChildren();
    const safeCount = state.routes.filter((route) => route.eligible).length;
    const blockedCount = state.routes.length - safeCount;
    $("model-count").textContent = state.routes.length + " models discovered";
    $("catalog-pill").textContent = safeCount + " verified · " + blockedCount + " blocked";
    $("catalog-detail").textContent = "Active Hermes provider: " + (state.activeProvider || "not specified") +
      ". " + safeCount + " model route(s) meet the private $0 policy.";
    const grouped = new Map();
    state.routes.forEach((route) => {
      if (!grouped.has(route.providerId)) grouped.set(route.providerId, []);
      grouped.get(route.providerId).push(route);
    });
    grouped.forEach((routes, providerId) => {
      const provider = state.providers.find((item) => item.id === providerId) || {};
      const card = document.createElement("div");
      card.className = "provider";
      const heading = document.createElement("strong");
      heading.textContent = String(provider.display_name || providerId || "Unknown provider");
      const detail = document.createElement("small");
      const allowed = routes.filter((route) => route.eligible).length;
      detail.textContent = allowed + " verified local / " + (routes.length - allowed) + " blocked · " +
        (provider.is_self_hosted === true ? "self-hosted" : "hosted or unverified");
      card.append(heading, detail);
      catalog.append(card);
    });
    if (!state.routes.length) {
      const empty = document.createElement("div");
      empty.className = "muted";
      empty.textContent = "No models were returned by the active Hermes profile.";
      catalog.append(empty);
    }
  }

  function populateModels(preferredRoute) {
    const select = $("model-select");
    select.replaceChildren();
    state.routes.forEach((route, index) => {
      const status = route.eligible ? "Verified private · $0" : "Blocked · cost not verified";
      const option = new Option(
        route.modelLabel + " · " + route.providerName + " · " + status,
        String(index)
      );
      option.disabled = !route.eligible;
      select.add(option);
    });
    const selectedIndex = preferredRoute ? state.routes.indexOf(preferredRoute) : -1;
    const firstEligible = state.routes.findIndex((route) => route.eligible);
    const index = selectedIndex >= 0 && state.routes[selectedIndex].eligible ? selectedIndex : firstEligible;
    if (index < 0) {
      select.value = state.routes.length ? "0" : "";
      select.disabled = true;
      $("route-button").disabled = true;
      setPill("model-pill", "No $0 route", "warn");
      $("policy-detail").textContent = "No verified private self-hosted model is available. Hosted and cost-unknown providers are blocked. Configure a local model endpoint in Hermes, then refresh.";
      return;
    }
    select.value = String(index);
    select.disabled = false;
    updateSelection();
  }

  function currentRoute() {
    const index = Number($("model-select").value);
    return Number.isInteger(index) ? state.routes[index] || null : null;
  }

  function updateSelection() {
    const route = currentRoute();
    const allowed = Boolean(route && route.eligible);
    $("route-button").disabled = !allowed;
    if (!route) {
      setPill("model-pill", "No route", "warn");
      $("policy-detail").textContent = "Select a verified private local model to continue.";
      return;
    }
    setPill("model-pill", allowed ? "Verified private" : "Blocked", allowed ? "good" : "warn");
    $("policy-detail").textContent = allowed ? route.reason :
      (route.reason || "This route is blocked by the $0 policy.");
    $("route-error").textContent = "";
  }

  function applyMode() {
    const mode = $("mode-select").value;
    const route = window.ANNEPolicy.selectRoute(state.routes, mode, state.activeProvider);
    if (route) {
      $("model-select").value = String(state.routes.indexOf(route));
    }
    updateSelection();
  }

  async function loadModels() {
    setPill("model-pill", "Refreshing", "warn");
    try {
      const payload = await getJson("/api/providers");
      state.providers = Array.isArray(payload.providers) ? payload.providers : [];
      state.activeProvider = payload.active_provider || null;
      state.routes = window.ANNEPolicy.buildRoutes(payload);
      renderCatalog();
      populateModels(window.ANNEPolicy.selectRoute(state.routes, $("mode-select").value, state.activeProvider));
    } catch (error) {
      state.providers = [];
      state.routes = [];
      $("model-select").replaceChildren(new Option("Model catalog unavailable", ""));
      $("model-select").disabled = true;
      $("route-button").disabled = true;
      $("model-count").textContent = "Unavailable";
      $("catalog-detail").textContent = error.message;
      setPill("catalog-pill", "Check failed", "bad");
      setPill("model-pill", "Unavailable", "bad");
    }
  }

  async function getCsrfToken() {
    const response = await fetch("/", { credentials: "same-origin", cache: "no-store" });
    if (!response.ok) throw new Error("Could not obtain the authenticated Hermes page context.");
    const html = await response.text();
    const match = html.match(/csrfToken:("(?:\\.|[^"\\])*")/);
    if (!match) {
      if (state.auth && state.auth.auth_enabled === false) return "";
      throw new Error("Hermes did not provide a CSRF token. Sign in and reload.");
    }
    return JSON.parse(match[1]);
  }

  async function openModelSession() {
    const route = currentRoute();
    if (!route || route.eligible !== true) return;
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
          model: route.modelId,
          model_provider: route.providerId,
          worktree: false
        })
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.error || "Hermes session creation failed (HTTP " + response.status + ").");
      }
      const sessionId = data && data.session && data.session.session_id;
      if (!sessionId) throw new Error("Hermes did not return a session ID.");
      window.location.assign("/session/" + encodeURIComponent(sessionId));
    } catch (error) {
      $("route-error").textContent = error.message;
      $("route-button").disabled = false;
      $("route-button").textContent = "Open model session";
    }
  }

  async function refreshAll() {
    await Promise.all([refreshHealth(), loadModels()]);
  }

  $("mode-select").addEventListener("change", applyMode);
  $("model-select").addEventListener("change", updateSelection);
  $("route-button").addEventListener("click", openModelSession);
  $("refresh-button").addEventListener("click", refreshAll);
  refreshAll();
  state.timer = window.setInterval(refreshAll, 30000);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") refreshAll();
  });
})();
