export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    // Rewrites your request to point to Leonardo's actual API
    const targetUrl = "https://cloud.leonardo.ai" + url.pathname;
    
    const modifiedRequest = new Request(targetUrl, {
      method: request.method,
      headers: request.headers,
      body: request.body,
    });

    // Leonardo AI requires these to verify the origin
    modifiedRequest.headers.set("Origin", "https://cloud.leonardo.ai");
    modifiedRequest.headers.set("Referer", "https://cloud.leonardo.ai");

    return fetch(modifiedRequest);
  },
};
