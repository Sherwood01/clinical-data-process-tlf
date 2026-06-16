export function register() {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = function (url, options = {}) {
    const urlStr = typeof url === "string" ? url : url instanceof URL ? url.href : url.url;

    // Log all fetch calls to debug the Stack Auth issue
    console.log("[instrumentation] fetch:", urlStr);

    const isStackAuthCall =
      typeof urlStr === "string" && urlStr.includes("8102");

    if (isStackAuthCall) {
      options = { ...options };
      options.headers = options.headers
        ? new Headers(options.headers)
        : new Headers();
      if (!options.headers.has("x-hexclave-access-type") && !options.headers.has("x-stack-access-type")) {
        console.log("[instrumentation] Adding x-stack-access-type: client to", urlStr);
        options.headers.set("x-stack-access-type", "client");
      }
    }

    return originalFetch.call(this, url, options);
  };

  console.log("[instrumentation] Fetch hook registered");
}
