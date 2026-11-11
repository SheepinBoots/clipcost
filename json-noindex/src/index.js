// Adds X-Robots-Tag: noindex to VidFare's JSON data files. Everything else passes through untouched.
export default {
  async fetch(request) {
    const res = await fetch(request);
    const url = new URL(request.url);
    if (!url.pathname.endsWith(".json")) return res;
    const out = new Response(res.body, res);
    out.headers.set("X-Robots-Tag", "noindex");
    return out;
  },
};
