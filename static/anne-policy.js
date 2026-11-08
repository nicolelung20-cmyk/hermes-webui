/* ANNE's fail-closed model eligibility policy. No network access or credentials. */
(function (root) {
  "use strict";

  function isPrivateHost(hostname) {
    const host = String(hostname || "").toLowerCase().replace(/^\[|\]$/g, "").replace(/\.$/, "");
    if (host === "localhost" || host.endsWith(".localhost") || host === "::1") return true;
    if (/^(fc|fd)[0-9a-f]{2}:/i.test(host) || /^fe[89ab][0-9a-f]:/i.test(host)) return true;

    const parts = host.split(".");
    if (parts.length !== 4 || parts.some((part) => !/^\d{1,3}$/.test(part) || Number(part) > 255)) return false;
    const octets = parts.map(Number);
    const [a, b] = octets;
    return a === 10 ||
      a === 127 ||
      (a === 172 && b >= 16 && b <= 31) ||
      (a === 192 && b === 168) ||
      (a === 169 && b === 254) ||
      (a === 100 && b >= 64 && b <= 127);
  }

  function isPrivateEndpoint(baseUrl) {
    if (typeof baseUrl !== "string" || !baseUrl.trim()) return false;
    try {
      const parsed = new URL(baseUrl);
      if (parsed.protocol !== "http:" && parsed.protocol !== "https:") return false;
      if (parsed.username || parsed.password) return false;
      return isPrivateHost(parsed.hostname);
    } catch (_error) {
      return false;
    }
  }

  function eligibility(provider) {
    if (!provider || provider.is_self_hosted !== true) {
      return { eligible: false, reason: "Hosted or cost-unknown provider is blocked by the $0 policy." };
    }
    if (!isPrivateEndpoint(provider.base_url)) {
      return { eligible: false, reason: "Private local endpoint could not be verified; route is blocked." };
    }
    return { eligible: true, reason: "Self-hosted model on a private endpoint; no hosted model API is used." };
  }

  function buildRoutes(providerPayload) {
    const providers = Array.isArray(providerPayload) ? providerPayload :
      (providerPayload && Array.isArray(providerPayload.providers) ? providerPayload.providers : []);
    const routes = [];
    providers.forEach((provider) => {
      if (!provider || typeof provider !== "object") return;
      const check = eligibility(provider);
      const models = Array.isArray(provider.models) ? provider.models : [];
      models.forEach((item) => {
        const model = typeof item === "string" ? { id: item, label: item } : item;
        if (!model || typeof model !== "object") return;
        const modelId = String(model.id || model.model || model.name || "").trim();
        if (!modelId) return;
        routes.push({
          providerId: String(provider.id || ""),
          providerName: String(provider.display_name || provider.id || "Unknown provider"),
          modelId,
          modelLabel: String(model.label || model.name || modelId),
          eligible: check.eligible,
          reason: check.reason
        });
      });
    });
    return routes;
  }

  function selectRoute(routes, mode, activeProvider) {
    if (!Array.isArray(routes)) return null;
    const safe = routes.filter((route) => route && route.eligible === true);
    if (!safe.length) return null;
    const normalizedMode = String(mode || "LOCAL").toUpperCase();
    if (!["FAST", "REASON", "LOCAL", "AUTO"].includes(normalizedMode)) return null;
    if (normalizedMode === "AUTO" && activeProvider) {
      const active = safe.find((route) => route.providerId === activeProvider);
      if (active) return active;
    }
    if (normalizedMode === "FAST") {
      const fast = safe.find((route) => /fast|mini|small|flash|instant|\b[1-4]b\b/i.test(route.modelId + " " + route.modelLabel));
      if (fast) return fast;
    }
    if (normalizedMode === "REASON") {
      const reason = safe.find((route) => /reason|think|thinking|\br1\b|deep/i.test(route.modelId + " " + route.modelLabel));
      if (reason) return reason;
    }
    return safe[0];
  }

  const api = { isPrivateHost, isPrivateEndpoint, eligibility, buildRoutes, selectRoute };
  root.ANNEPolicy = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
