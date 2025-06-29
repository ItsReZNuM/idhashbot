# Telegram API ID & Hash Bot 🤖

Welcome to the **Telegram API ID & Hash Bot**! This is a Telegram bot designed to help developers and users easily obtain their Telegram **API ID** and **API Hash** securely through the official Telegram website. It also includes an admin broadcast feature for sending messages to all users. 🚀

---

## ✨ Features
- 📱 **Fetch API Credentials**: Users can provide their phone number to receive their Telegram API ID and API Hash.
- 🔒 **Secure Process**: No phone numbers are stored; the process is handled securely via Telegram's official API.
- 📢 **Admin Broadcast**: Admins can send messages to all registered users.
- ⏱ **Rate Limiting**: Prevents spam by limiting message frequency.
- 🌍 **Persian Language Support**: User-friendly messages in Persian for a better experience.

---

## 🛠 Installation
Follow these steps to set up and run the bot locally:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/ItsReZNuM/idhashbot
   cd idhashbot
   ```

2. **Install Dependencies**:
   Ensure you have Python 3.8+ installed. Then, install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment**:
   - Replace the `BOT_TOKEN` in `idhashbot.py` with your Telegram bot token obtained from [@BotFather](https://t.me/BotFather).
   - Update `ADMIN_USER_IDS` in `idhashbot.py` with the Telegram user ID(s) of the admin(s).

4. **Run the Bot**:
   ```bash
   python idhashbot.py
   ```

---

## 📖 Usage
1. Start the bot by sending the `/start` command.
2. Share your phone number (e.g., `+989123456789`) or use the "Share Contact" button.
3. Enter the verification code sent by Telegram.
4. Receive your **API ID**, **API Hash**, **Public Key**, and **Production Configuration**! 🎉
5. Admins can use the "Broadcast Message 📢" button to send messages to all users.

---

## ⚙️ Commands
- `/start`: Begins the process to fetch API credentials.
- `/cancel`: Cancels the current process and resets the state.

---

## 🧑‍💻 For Admins
- **Broadcast Feature**: Admins (defined in `ADMIN_USER_IDS`) can send messages to all registered users using the "Broadcast Message 📢" button.
- **User Management**: User data (ID and username) is stored in `users.json` for broadcast purposes.

---

## 📋 Requirements
The following Python packages are required:
- `pyTelegramBotAPI` - For Telegram bot functionality
- `requests` - For HTTP requests to Telegram's API
- `beautifulsoup4` - For parsing HTML responses
- `pytz` - For handling time zones

See `requirements.txt` for details.

---

## 🔐 Security Notes
- Phone numbers are not stored locally; they are only used temporarily to communicate with Telegram's official API.
- Ensure your bot token and admin IDs are kept secure and not exposed in public repositories.

---

## 🤝 Contributing
Contributions are welcome! 🙌 Feel free to submit issues or pull requests to improve the bot. Please follow these steps:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m 'Add your feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

---


## 📬 Contact
For questions or support, reach out via [GitHub Issues](https://github.com/ItsReZNuM/idhashbot) or contact the maintainer on Telegram.
- Telegram Bot : @ReZIdHashBot
- Me: t.me/ItsReZNuM

Happy coding! 🚀