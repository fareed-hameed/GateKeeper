/*
 * aegis-identity.js — Persistent device identity for AEGIS
 *
 * Strategy:
 *   - Random UUID is the stable device ID (never drifts across browser updates).
 *   - Evercookie persists the UUID across many client-side stores (cookie,
 *     localStorage, sessionStorage, IndexedDB, Web SQL, window.name, userData).
 *   - ThumbmarkJS produces a browser signature used only as a soft audit
 *     field — it is NOT the identity and does NOT gate access, so signature
 *     drift across browser updates cannot lock the user out.
 *
 * Globals exposed:
 *   window.gkFingerprint    — stable UUID string
 *   window.gkSignature      — thumbmark hash (nullable, non-blocking)
 *   window.gkIdentityReady  — Promise<string> resolves to the UUID
 *
 * Back-compat:
 *   Calls window.onFingerprintReady() once window.gkFingerprint is set.
 */
(function () {
    'use strict';

    var KEY = 'aegis_did';
    var LEGACY_KEY = 'aegis_device_id'; // from the old FingerprintJS implementation

    function uuidv4() {
        if (window.crypto && typeof window.crypto.randomUUID === 'function') {
            return window.crypto.randomUUID();
        }
        var b = new Uint8Array(16);
        (window.crypto || window.msCrypto).getRandomValues(b);
        b[6] = (b[6] & 0x0f) | 0x40;
        b[8] = (b[8] & 0x3f) | 0x80;
        var h = [];
        for (var i = 0; i < 16; i++) {
            h.push(b[i].toString(16).padStart(2, '0'));
        }
        return (
            h.slice(0, 4).join('') + '-' +
            h.slice(4, 6).join('') + '-' +
            h.slice(6, 8).join('') + '-' +
            h.slice(8, 10).join('') + '-' +
            h.slice(10, 16).join('')
        );
    }

    function initEvercookie() {
        if (typeof evercookie !== 'function') return null;
        try {
            // Enable client-side-only backends. Everything requiring a server
            // endpoint (png, etag, cache) or deprecated plugins (lso/flash,
            // silverlight, java) stays off by default.
            return new evercookie({
                history: false,
                java: false,
                silverlight: false,
                lso: false,
                db: true,
                idb: true
            });
        } catch (e) {
            return null;
        }
    }

    function ecGet(ec, key) {
        return new Promise(function (resolve) {
            var done = false;
            var finish = function (v) {
                if (done) return;
                done = true;
                resolve(v || null);
            };
            try {
                ec.get(key, function (value) { finish(value); });
            } catch (e) {
                finish(null);
            }
            // Evercookie may hang if a backend stalls — cap the wait.
            setTimeout(function () { finish(null); }, 2500);
        });
    }

    function ecSet(ec, key, value) {
        try { ec.set(key, value); } catch (e) { /* swallow */ }
    }

    function lsGet(key) {
        try { return localStorage.getItem(key); } catch (e) { return null; }
    }

    function lsSet(key, value) {
        try { localStorage.setItem(key, value); } catch (e) { /* swallow */ }
    }

    function cookieGet(key) {
        try {
            var m = document.cookie.match(new RegExp('(?:^|; )' + key + '=([^;]*)'));
            return m ? decodeURIComponent(m[1]) : null;
        } catch (e) { return null; }
    }

    function cookieSet(key, value) {
        try {
            // ~10 years, scoped to site, Lax to survive normal top-level nav.
            var maxAge = 60 * 60 * 24 * 365 * 10;
            document.cookie =
                key + '=' + encodeURIComponent(value) +
                '; path=/; max-age=' + maxAge + '; SameSite=Lax' +
                (location.protocol === 'https:' ? '; Secure' : '');
        } catch (e) { /* swallow */ }
    }

    async function computeSignature() {
        try {
            if (typeof ThumbmarkJS === 'undefined') return null;
            var tm = new ThumbmarkJS.Thumbmark();
            var res = await tm.get();
            if (!res) return null;
            return res.thumbmark || res.hash || null;
        } catch (e) {
            return null;
        }
    }

    window.gkFingerprint = null;
    window.gkSignature = null;

    window.gkIdentityReady = (async function () {
        var ec = initEvercookie();

        // 1. Look for an existing UUID in any available store.
        var did = null;
        if (ec) did = await ecGet(ec, KEY);
        if (!did) did = lsGet(KEY);
        if (!did) did = cookieGet(KEY);
        // Legacy FingerprintJS visitor-id — if present, reuse it so previously
        // enrolled devices still recognised on this browser carry over.
        if (!did) did = lsGet(LEGACY_KEY);

        // 2. Generate if absent.
        if (!did) {
            did = uuidv4();
        }

        // 3. Write back to every store so any cleared backend is re-seeded.
        if (ec) ecSet(ec, KEY, did);
        lsSet(KEY, did);
        cookieSet(KEY, did);

        window.gkFingerprint = did;

        // 4. Fire the back-compat callback for existing templates.
        if (typeof window.onFingerprintReady === 'function') {
            try { window.onFingerprintReady(); } catch (e) { /* swallow */ }
        }

        // 5. Compute signature in the background — never gates readiness.
        computeSignature().then(function (sig) { window.gkSignature = sig; });

        return did;
    })();
})();
