# Telegram API ID & Hash Bot 🤖

A modern, secure, and multilingual Telegram bot designed to help users and developers retrieve their Telegram **API ID** and **API Hash** automatically from `my.telegram.org`.

---

## ✨ Features
- 📱 **Automated API Retrieval**: Seamlessly fetches API ID, API Hash, Public Keys, and Production Configuration.
- ⚙️ **Automatic App Creation**: Automatically creates a Telegram application if the account does not yet have one registered (matching the latest `ApiIDHash` engine).
- 🌐 **Multilingual Support**: Full support for **Persian (فارسی)**, **English**, and **Russian (Русский)** with one-click language switching.
- 🔒 **Zero Credential Storage**: Requests go directly to `my.telegram.org` over encrypted HTTPS within temporary user sessions. No numbers, hashes, or passwords are saved.
- 📢 **Admin Broadcast**: Admins can broadcast announcements to all users with live delivery progress.
- ⏱ **Rate Limiting**: Built-in anti-spam protection against flooding.
- 🛡️ **Resilient Scraping**: Multi-layer DOM and regex extraction fallbacks adapted to Telegram's web interface changes.

---

## 🛠 Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/ItsReZNuM/idhashbot
   cd idhashbot
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Create or edit `.env`:
   ```env
   TOKEN="YOUR_BOT_TOKEN_FROM_BOTFATHER"
   ADMIN_USER_IDS="123456789,987654321"
   DATABASE_NAME="users.db"
   ```

4. **Run Unit Tests**:
   ```bash
   python -m pytest tests/
   ```

5. **Start the Bot**:
   ```bash
   python main.py
   ```

---

## 📖 Usage
1. Send `/start` to the bot.
2. Select your preferred language (🇮🇷 فارسی, 🇬🇧 English, or 🇷🇺 Русский).
3. Send your phone number with country code (e.g. `+989123456789`, `+79123456789`, `+12025550143`) or use the "Share Phone Number" button.
4. Telegram will send an official confirmation code to your Telegram app.
5. Enter the code or forward the service notification to the bot.
6. The bot retrieves and sends your **API ID** and **API Hash**! 🎉

---

## ⚙️ Commands
- `/start`: Starts or restarts the bot.
- `/lang` or `/language`: Opens language switcher (Persian, English, Russian).
- `/help`: Displays help and instructions in the active language.
- `/cancel`: Cancels any active authentication flow and clears temporary session.
- `/alive`: Health check to verify bot responsiveness.
- `/broadcast`: Admin command to broadcast messages to all registered users.

---

## 📬 Contact
- **Developer**: [@ItsReZNuM](https://t.me/ItsReZNuM)
- **Bot**: [@ReZIdHashBot](https://t.me/ReZIdHashBot)