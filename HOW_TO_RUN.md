# HOW TO RUN - AI Outbound Caller

Complete guide to run your AI-powered outbound calling system with voice testing sandbox.

---

## Prerequisites

- Python 3.11+ installed
- Node.js and pnpm installed
- LiveKit account and project set up
- Git Bash or terminal

---

## Quick Start - 3 Components

You need to run **3 things** to use this system:

1. **The AI Agent (Backend)** - Handles the phone calls
2. **Voice Testing Sandbox (Frontend)** - Test AI voice in browser without phone calls
3. **Dispatch Command** - Actually make phone calls

---

## 1. START THE AI AGENT (Always Run First)

**Terminal 1:**

```bash
cd /mnt/d/Coding-projects/outbound-caller-python-main
source venv-wsl/bin/activate
python3 agent.py start
```

**What you should see:**

```json
{"message": "starting worker", "level": "INFO", ...}
{"message": "registered worker", "id": "AW_xxxxx", ...}
```

**Success:** When you see `"registered worker"` - your agent is ready!

**Keep this terminal running!** Don't close it.

---

## 2. LAUNCH THE VOICE TESTING SANDBOX (Optional - For Testing)

**Terminal 2:**

```bash
# Voice test sandbox not yet set up - create it with:
# lk app create --template agent-starter-react
# Then: cd voice-test && pnpm install && pnpm dev
```

**What you should see:**

```text
Next.js 14.x.x
- Local:   http://localhost:3000
```

**Success:** Open your browser to `http://localhost:3000`

**Test your AI agent:**

- Click the microphone button
- Start talking to test the AI voice assistant
- No phone calls needed - just browser testing!

---

## 3. MAKE ACTUAL PHONE CALLS

### Option A: Using Command Line (Git Bash)

**Terminal 3:**

```bash
cd /mnt/d/Coding-projects/outbound-caller-python-main

lk dispatch create \
  --new-room \
  --agent-name outbound-caller \
  --metadata '{"phone_number": "+1234567890", "transfer_to": "+0987654321"}'
```

**Replace:**

- `+1234567890` = Phone number to call
- `+0987654321` = Transfer number (optional)

### Option B: Using LiveKit Dashboard (Easier)

1. Go to: <https://cloud.livekit.io/>
2. Login and select: **ai-assistant-calling-project**
3. Navigate to: **Agents** -> **Dispatch** (or **Rooms** -> **Create Room**)
4. Fill in:
   - **Agent Name:** `outbound-caller`
   - **Metadata:**

     ```json
     {"phone_number": "+1234567890", "transfer_to": "+0987654321"}
     ```

5. Click **Create** or **Dispatch**

**Success:** The phone will ring and the AI agent will start talking!

---

## What the AI Agent Does

When someone answers:

- Introduces itself as a dental scheduling assistant
- Tries to confirm an appointment for "Jayden" on "next Tuesday at 3pm"
- Can answer questions about availability
- Can transfer to a human if requested
- Detects voicemail and hangs up

---

## Monitoring and Debugging

### View Live Status

- **Dashboard:** <https://cloud.livekit.io/>
- **Your Project:** ai-assistant-calling-project
- **Check:** Agents tab to see worker status
- **Monitor:** Rooms tab to see active calls

### Check Logs

Look at Terminal 1 (where agent is running) for real-time logs:

```json
{"message": "connecting to room", ...}
{"message": "participant joined", ...}
```

---

## Stopping Everything

1. **Stop the Agent:** Press `Ctrl+C` in Terminal 1
2. **Stop the Sandbox:** Press `Ctrl+C` in Terminal 2
3. **Calls automatically end** when agent stops

---

## Configuration

### Main Config File: `.env.local`

Copy `.env.example` to `.env.local` and fill in your credentials:

```bash
# LiveKit Configuration (Get from https://cloud.livekit.io/)
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
LIVEKIT_SIP_URI=sip:your-sip-uri.sip.livekit.cloud

# OpenAI API Key (Required for Realtime API)
OPENAI_API_KEY=sk-proj-your_openai_key

# SIP Trunk ID (Get from LiveKit dashboard after trunk setup)
SIP_OUTBOUND_TRUNK_ID=ST_your_trunk_id

# Optional: For alternative STT/TTS providers (if not using Realtime API)
DEEPGRAM_API_KEY=your_deepgram_key
CARTESIA_API_KEY=your_cartesia_key

# Twilio Credentials (For trunk setup only)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_TO_NUMBER=+0987654321
```

---

## Troubleshooting

### Agent Won't Start - TimeoutError on Windows/MINGW64

- **Error:** `TimeoutError` during inference executor initialization
- **Root Cause:** LiveKit agents' IPC system doesn't work on Windows/MINGW64
- **Solutions:**
  1. **Use WSL2 (Recommended):** Run the agent in Windows Subsystem for Linux

     ```bash
     # In WSL2 terminal:
     cd /mnt/d/Coding-projects/outbound-caller-python-main
     source venv-wsl/bin/activate
     python3 agent.py start
     ```

  2. **Use Docker:** Run in a Linux container
  3. **Deploy to Cloud:** Use a Linux server or cloud platform

- **Why this happens:** The inference executor uses Unix sockets for IPC, which aren't fully compatible with Windows

### Can't Make Calls

- **Check:** Is the agent running? (Terminal 1 should show "registered worker")
- **Check:** Is your SIP trunk active? Check dashboard
- **Check:** Do you have Twilio credits?

### Voice Sandbox Not Working

- **Check:** Is the agent running? (Terminal 1)
- **Check:** Did you run `pnpm install` first?
- **Check:** Browser console for errors (F12)

### Command `lk` Not Found

- **Solution 1:** Use the dashboard instead (easier!)
- **Solution 2:** Reinstall LiveKit CLI: `winget install LiveKit.LiveKitCLI`

---

## Summary Checklist

Before making your first call:

- [ ] Agent is running (Terminal 1 shows "registered worker")
- [ ] Sandbox is running (optional, Terminal 2, <http://localhost:3000>)
- [ ] You have the phone number you want to call
- [ ] You've tested in sandbox first (recommended)
- [ ] You're ready to dispatch via CLI or dashboard

---

## Success

You now have a fully functional AI-powered outbound calling system!

**Next Steps:**

- Customize the agent's greeting in `agent.py` (line 49)
- Change the appointment details (line 179-180)
- Adjust the AI voice/personality in `agent.py` (line 187-191)
- Add your own function tools for custom features

---

## Need Help?

- **LiveKit Docs:** <https://docs.livekit.io/agents/>
- **Dashboard:** <https://cloud.livekit.io/>
- **Issues:** Check Terminal 1 logs first

---

**Created:** 2025-10-14
**Project:** AI Assistant Calling - Outbound Caller Python
**Agent Name:** outbound-caller
**Worker ID:** Check dashboard for current ID
