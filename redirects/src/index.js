// Permanent redirects for a few typo / alternate paths on vidfare.com.
// Anything not in REDIRECTS is passed through to the origin.
const REDIRECTS = {
  "/about-us": "/about/",
  "/about-us/": "/about/",
};

const CANONICAL_ORIGIN = "https://vidfare.com";

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const target = REDIRECTS[url.pathname];
    if (!target) return fetch(request);
    const dest = new URL(target, CANONICAL_ORIGIN);
    dest.search = url.search;
    return Response.redirect(dest.toString(), 301);
  },
};
