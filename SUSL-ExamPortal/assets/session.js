/* ExamPortal — shared session + route guard used by every portal.
   The session lives in localStorage with an 8-hour expiry (same lifetime as the
   lecturer API token). NOTE: this is a front-end convenience layer only — real
   authorisation must always be enforced by the server. */
(function (w) {
  "use strict";
  var KEY = "susl_session";
  var TTL = 8 * 60 * 60 * 1000;

  // Project root URL, derived from this script's own location (…/assets/session.js)
  var scriptSrc = (document.currentScript && document.currentScript.src) || "";
  var ROOT = scriptSrc.replace(/assets\/session\.js(\?.*)?$/, "");

  var HOME = { admin: "admin/index.html", lecturer: "lecturer/index.html", student: "student/index.html" };

  function read() {
    try {
      var s = JSON.parse(localStorage.getItem(KEY) || "null");
      if (!s || !s.exp || Date.now() > s.exp) { localStorage.removeItem(KEY); return null; }
      return s;
    } catch (e) { return null; }
  }

  var S = {
    root: ROOT,
    get: read,
    set: function (role, user) {
      try { localStorage.setItem(KEY, JSON.stringify({ role: role, user: user || {}, exp: Date.now() + TTL })); } catch (e) {}
    },
    clear: function () {
      try {
        localStorage.removeItem(KEY);
        localStorage.removeItem("examportal_token");   // lecturer portal keys
        localStorage.removeItem("examportal_user");
      } catch (e) {}
    },
    homeFor: function (role) { return ROOT + (HOME[role] || ""); },
    loginUrl: function () { return ROOT + "index.html"; },
    /* Redirect to the sign-in page unless a valid session for `role` exists. */
    require: function (role) {
      var s = read();
      if (!s || s.role !== role) { w.location.replace(S.loginUrl()); return null; }
      return s;
    },
    /* Clear everything and go back to the sign-in page. */
    signOut: function () { S.clear(); w.location.href = S.loginUrl(); }
  };
  w.SUSLSession = S;
})(window);
