/* VidFare GoatCounter events. Cookie-free: nothing is stored in the browser.
 * Sends goatcounter.count({path, title, event:true}) for:
 *   newsletter-signup/<page>             newsletter form submit
 *   outbound/<vendor>/<page>             click to a vendor or deal page
 *   outbound-affiliate/<vendor>/<page>   same, when the link is an affiliate link
 *   sponsor-click/<slot>/<page>          click inside a sponsor slot
 *   advertise-cta/<cta>/<page>           click on an /advertise/ link or the advertise email
 *   campaign/<source>/<medium>/<campaign> landing with utm_* parameters
 * See docs/analytics.md. If count.js is blocked or not loaded, nothing happens
 * and links and forms work as normal. */
(function () {
  'use strict';
  if (!document.addEventListener) return;
  var HOSTS = {"ai.google.dev":"google-gemini-api","atlascloud.ai":"atlas-cloud","docs.dev.runwayml.com":"runway-api","fal.ai":"fal","higgsfield.ai":"higgsfield","kling.ai":"kling-api","krea.ai":"krea","magnific.com":"magnific","open.higgsfield.ai":"higgsfield-api","replicate.com":"replicate","runwayml.com":"runway"};
  var SITE = { 'vidfare.com': 1, 'www.vidfare.com': 1 };
  var me = document.currentScript || document.querySelector('script[data-vf-page]');
  function slug(s, n) {
    s = String(s || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
    return s.slice(0, n || 60).replace(/-+$/, '');
  }
  function pageSlug() {
    if (me && me.getAttribute('data-vf-page')) return me.getAttribute('data-vf-page');
    var p = location.pathname.replace(/(index)?\.html$/, '').replace(/^\/+|\/+$/g, '');
    return slug(p.replace(/\//g, '-'), 80) || 'home';
  }
  var PAGE = pageSlug();
  function ready() {
    return !!(window.goatcounter && typeof window.goatcounter.count === 'function');
  }
  function send(path, title) {
    if (!ready()) return false;
    try { window.goatcounter.count({ path: path, title: title, event: true }); return true; }
    catch (e) { return false; }
  }
  function host(u) {
    var h = (u.hostname || '').toLowerCase();
    return h.indexOf('www.') === 0 ? h.slice(4) : h;
  }
  function vendor(u) {
    var h = host(u);
    if (HOSTS[h]) return HOSTS[h];
    var parts = h.split('.');
    for (var i = 1; i < parts.length - 1; i++) {
      var parent = parts.slice(i).join('.');
      if (HOSTS[parent]) return HOSTS[parent];
    }
    return slug(h) || 'unknown';
  }
  function modelOf(a) {
    if (a.getAttribute('data-vf-model')) return a.getAttribute('data-vf-model');
    var row = a.closest && a.closest('tr');
    var m = row && row.querySelector('a[href*="/models/"]');
    var hit = m && /\/models\/([a-z0-9-]+)\//.exec(m.getAttribute('href') || '');
    if (hit) return hit[1];
    hit = /^models-([a-z0-9-]+)$/.exec(PAGE);
    return hit ? hit[1] : '';
  }
  function onClick(ev) {
    if (ev.type === 'auxclick' && ev.button !== 1) return;
    var a = ev.target && ev.target.closest && ev.target.closest('a[href]');
    if (!a) return;
    var u;
    try { u = new URL(a.href, location.href); } catch (e) { return; }
    var slot = a.closest('[data-sponsor]');
    var cta = a.getAttribute('data-vf-cta');
    if (slot && !cta && u.pathname.replace(/\/$/, '') !== '/advertise') {
      var s = a.getAttribute('data-vf-sponsor') || slug(slot.getAttribute('data-sponsor')) || 'unknown';
      send('sponsor-click/' + s + '/' + PAGE, 'Sponsor click: ' + s + ' on ' + PAGE);
      return;
    }
    var toAdvertise = (u.protocol === 'http:' || u.protocol === 'https:') &&
      (SITE[host(u)] || host(u) === host(location)) && u.pathname.replace(/\/$/, '') === '/advertise';
    if (cta || toAdvertise) {
      cta = cta || (slot ? 'sponsor-slot-' + slug(slot.getAttribute('data-sponsor')) : (a.closest('footer') ? 'footer-link' : 'inline-link'));
      send('advertise-cta/' + slug(cta) + '/' + PAGE, 'Advertise CTA: ' + cta + ' on ' + PAGE);
      return;
    }
    if (u.protocol !== 'http:' && u.protocol !== 'https:') return;
    if (SITE[host(u)] || host(u) === host(location)) return;
    var v = a.getAttribute('data-vf-vendor') || vendor(u);
    var aff = a.getAttribute('data-vf-affiliate') === '1' ||
      (!slot && ((' ' + (a.getAttribute('rel') || '') + ' ').indexOf(' sponsored ') > -1 || u.searchParams.has('fpr')));
    var model = modelOf(a);
    var kind = aff ? 'outbound-affiliate' : 'outbound';
    send(kind + '/' + slug(v) + '/' + PAGE,
      (aff ? 'Affiliate click: ' : 'Outbound click: ') + v + (model ? ' (' + model + ')' : '') + ' on ' + PAGE);
  }
  function onSubmit(ev) {
    var f = ev.target;
    if (!f || f.tagName !== 'FORM') return;
    if (f.getAttribute('data-vf-event') !== 'newsletter-signup' && !f.hasAttribute('data-sv-form')) return;
    send('newsletter-signup/' + PAGE, 'Newsletter sign-up submit on ' + PAGE);
  }
  document.addEventListener('click', onClick, true);
  document.addEventListener('auxclick', onClick, true);
  document.addEventListener('submit', onSubmit, true);

  // GoatCounter already records utm_campaign/utm_source from the page view
  // (count.js sends location.search). This extra event keeps utm_medium too.
  function campaign() {
    var q;
    try { q = new URLSearchParams(location.search); } catch (e) { return; }
    var c = slug(q.get('utm_campaign') || q.get('campaign'));
    if (!c) return;
    var src = slug(q.get('utm_source') || q.get('source') || q.get('ref') || 'none', 30) || 'none';
    var med = slug(q.get('utm_medium') || 'none', 30) || 'none';
    var tries = 0;
    (function go() {
      if (send('campaign/' + src + '/' + med + '/' + c, 'Campaign landing: ' + src + ' / ' + med + ' / ' + c + ' on ' + PAGE)) return;
      if (++tries < 40) setTimeout(go, 250);
    })();
  }
  campaign();
})();
