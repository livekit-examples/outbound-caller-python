# Running Claude Sonnet 4 Agent

## Important: Must Use WSL2 (Not Windows)

The Claude Sonnet 4 agent uses the **pipelined approach** with:

- Deepgram (Speech-to-Text)
- Claude Sonnet 4 (LLM)
- Cartesia (Text-to-Speech)
- Silero (Voice Activity Detection)

This requires the inference executor which **only works in Unix environments (WSL2/Linux/macOS)**.

## Setup in WSL2

### 1. Open WSL2 Terminal

```bash
wsl
```

### 2. Navigate to Project

```bash
cd /mnt/d/Coding-Projects/outbound-caller-python
```

### 3. Activate Virtual Environment

If you haven't created one yet:

```bash
python3 -m venv venv
```

Then activate:

```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Start the Agent

```bash
./start-agent.sh start
```

**Wait for:** `"registered worker outbound-caller"` message

## Making a Call

### 1. Go to LiveKit Dashboard

<https://cloud.livekit.io/>

### 2. Navigate to Your Agent

- Click on your project
- Go to "Agents" section
- Find "outbound-caller"

### 3. Click "Dispatch"

### 4. Enter Phone Number in E.164 Format

```text
+19415180701
```

### 5. Click Dispatch

**Your phone will ring!** Answer it to talk to the Claude-powered health insurance specialist.

## What You'll Experience

- **Voice:** Professional British male narrator
- **AI:** Claude Sonnet 4 (superior reasoning)
- **Expertise:** Comprehensive health insurance knowledge
- **Topics:** HMO, PPO, Medicare, Medicaid, coverage options, claims, compliance

## Troubleshooting

### "ImportError: cannot import name 'anthropic'"

- You're running in Windows/MINGW64
- Solution: Use WSL2 (see steps above)

### "TimeoutError during inference executor"

- The agent needs Unix environment
- Solution: Use WSL2

### Agent doesn't start

```bash
# Check if dependencies are installed
pip list | grep livekit

# Reinstall if needed
pip install -r requirements.txt --force-reinstall
```

### Phone doesn't ring

- Check .env.local has correct SIP_OUTBOUND_TRUNK_ID
- Verify phone number is in E.164 format (+1234567890)
- Check LiveKit dashboard for error messages

## Switching Back to OpenAI Realtime API

If you want to use the simpler OpenAI approach (works on Windows):

Edit `agent.py` around line 338 and swap the commented sections:

```python
# Comment out Claude configuration
# session = AgentSession(
#     turn_detection=EnglishModel(),
#     vad=silero.VAD.load(),
#     stt=deepgram.STT(),
#     tts=cartesia.TTS(voice="79f8b5fb-2cc8-479a-80df-29f7a7cf1a3e"),
#     llm=anthropic.LLM(model="claude-sonnet-4-20250514"),
# )

# Uncomment OpenAI configuration
session = AgentSession(
    llm=openai.realtime.RealtimeModel(
        voice="echo",
        temperature=0.8,
    ),
)
```

Then you can run from Windows.
