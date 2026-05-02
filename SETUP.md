# Configuration Discord Bot - Guide d'Activation

## ÉTAPE REQUISE : Activer les Privileged Intents

Pour que le bot fonctionne avec les commandes `!`, vous **DEVEZ** activer les intents dans Discord Developer Portal.

##  Instructions Pas à Pas

### 1️⃣ Allez sur Discord Developer Portal
```
https://discord.com/developers/applications
```

### 2️⃣ Sélectionnez votre Application (Bot)
- Cliquez sur votre application dans la liste

### 3️⃣ Allez dans l'onglet "Bot"
- Menu gauche → Cliquez sur "Bot"

### 4️⃣ Trouvez "Privileged Gateway Intents"
Cherchez la section **"Privileged Gateway Intents"** dans la page

### 5️⃣ Activez les 2 Intents Requis
Cliquez sur les boutons pour activer :
- **Message Content Intent** - Permet au bot de lire le contenu des messages pour les commandes `!`
- **Server Members Intent** - Permet au bot d'accéder aux informations des membres

### 6️⃣ Sauvegardez
Cliquez sur **"Save Changes"** en bas de la page

## Vérification

Après avoir activé les intents, relancez le bot :

```bash
cd /home/klopi/Bureau/botdc
.venv/bin/python main.py
```

Vous devriez voir :
```
Bot logged in as YourBotName#9999
refix: !
Ready, use ! to access commands
```

## Utiliser les Commandes

Une fois le bot connecté, utilisez les commandes avec le préfixe `!` :

```
!kick @user [raison]      - Expulser un utilisateur
!ban @user [raison]       - Bannir un utilisateur
!warn @user [raison]      - Avertir un utilisateur
!mute @user [durée]       - Rendre muet (10m, 1h, 2d)
!unmute @user             - Retirer le silence
!warnings [@user]         - Voir les avertissements
!clearwarnings @user      - Supprimer les avertissements
```

## Troubleshooting

**Q: Le bot ne répond pas aux commandes**
A: Vérifiez que les Privileged Intents sont activés dans le Developer Portal

**Q: "Shard ID None is requesting privileged intents..."**
A: C'est le message d'erreur que vous aviez. Cela signifie que vous n'avez pas activé les intents. Suivez les étapes ci-dessus.

**Q: Ça prend combien de temps?**
A: Les intents se synchronisent immédiatement. Le bot redémarre automatiquement.

---

**Besoin d'aide?** Consultez la documentation officielle:
https://discord.com/developers/docs/topics/gateway
