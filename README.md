# Study Assistant - Privacy-First AI Learning Companion

A secure, privacy-focused AI study assistant that runs entirely in your browser with optional edge computing support.

## Features

- 🔒 **100% Private by Default** - All processing happens locally in your browser
- 🧠 **Smart Tutoring** - Guides learning without giving direct answers
- 📱 **Works Offline** - Full functionality even without internet
- 🔐 **End-to-End Encryption** - Optional encryption for all communications
- 💾 **Local Storage Only** - Your data never leaves your device
- 🌐 **No Tracking** - Zero analytics, cookies, or user tracking

## Quick Start

### Option 1: Use GitHub Pages (Recommended)

1. Fork this repository
2. Go to Settings → Pages
3. Enable GitHub Pages from main branch
4. Access at: `https://YOUR-USERNAME.github.io/YOUR-REPO-NAME`

### Option 2: Local Development

```bash
# Clone the repository
git clone https://github.com/YOUR-USERNAME/study-assistant.git
cd study-assistant

# Start a local server
python3 -m http.server 8080
# Or with Node.js
npx http-server -p 8080

# Open in browser
open http://localhost:8080
```

## Privacy Architecture

### Local-Only Mode (Default)
- All processing happens in the browser
- Uses IndexedDB for persistence
- No external API calls
- Works completely offline

### Edge Function Mode (Optional)
- Cloudflare Workers for enhanced processing
- No automatic logging
- Ephemeral processing only
- Optional client-side encryption

### Peer-to-Peer Mode (Experimental)
- Direct WebRTC connections
- No central server
- End-to-end encrypted

## File Structure

```
/
├── index.html          # Original interface
├── index-secure.html   # Privacy-first interface
├── secure-chat.js      # Core chat implementation
├── edge-worker.js      # Cloudflare Worker (optional)
├── service-worker.js   # Offline support
└── manifest.json       # PWA configuration
```

## Deployment Options

### GitHub Pages (Free, Easy)
- Push to GitHub
- Enable Pages in settings
- No configuration needed

### Cloudflare Pages (Free, Fast)
- Connect GitHub repo
- Automatic deployments
- Global CDN

### Self-Hosted (Maximum Privacy)
- Deploy to your own server
- Complete control
- Optional Tor hidden service

## Security Features

- Content Security Policy enforced
- No external dependencies
- All resources self-hosted
- Optional encryption layer
- No cookies or tracking
- Secure headers configured

## Data Management

### Export Your Data
- Click "Export" to download all data as JSON
- Includes chat history, patterns, and settings
- Standard format for easy backup

### Import Previous Data
- Click "Import" to restore from backup
- Maintains all learning patterns
- Seamless continuation

### Clear All Data
- Complete removal from device
- No cloud backups to worry about
- Fresh start anytime

## Contributing

We welcome contributions that enhance privacy and learning features!

1. Fork the repository
2. Create a feature branch
3. Implement privacy-first features
4. Submit a pull request

## Privacy Commitment

This project is committed to user privacy:

- ✅ No analytics or tracking
- ✅ No external API dependencies
- ✅ No data collection
- ✅ No advertisements
- ✅ No user accounts required
- ✅ Fully functional offline

## License

MIT License - Use freely while respecting user privacy

## Support

For questions or issues, please open a GitHub issue. 

Remember: Your learning journey is yours alone. This tool ensures it stays that way.

---

*Built with 💜 for students who value their privacy*