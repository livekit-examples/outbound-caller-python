# Python Outbound Call Agent

[![LiveKit logo](/.github/assets/livekit-mark.png)](https://livekit.io/)

[LiveKit Agents Docs](https://docs.livekit.io/agents/overview/) |
[LiveKit Cloud](https://livekit.io/cloud) |
[Blog](https://blog.livekit.io/)

This example demonstrates an full workflow of an AI agent that makes outbound calls. It uses LiveKit SIP and Python [Agents Framework](https://github.com/livekit/agents).

It can use a pipeline of STT, LLM, and TTS models, or a realtime speech-to-speech model. (such as ones from OpenAI and Gemini).

This example builds on concepts from the [Outbound Calls](https://docs.livekit.io/agents/start/telephony/#outbound-calls) section of the docs. Ensure that a SIP outbound trunk is configured before proceeding.

---

## HOW TO RUN - START HERE

**Complete step-by-step guide with:**

- Running the AI agent
- Testing with voice sandbox
- Making real phone calls
- Troubleshooting guide

**[Click here to get started](./HOW_TO_RUN.md)**

---

## Features

This example demonstrates the following features:

- Making outbound calls
- Detecting voicemail
- Looking up availability via function calling
- Transferring to a human operator
- Detecting intent to end the call
- Uses Krisp background voice cancellation to handle noisy environments

## Dev Setup

Clone the repository and install dependencies to a virtual environment:

```shell
git clone https://github.com/livekit-examples/outbound-caller-python.git
cd outbound-caller-python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python agent.py download-files
```

Set up the environment by copying `.env.example` to `.env.local` and filling in the required values:

- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `OPENAI_API_KEY`
- `SIP_OUTBOUND_TRUNK_ID`
- `DEEPGRAM_API_KEY` - optional, only needed when using pipelined models
- `CARTESIA_API_KEY` - optional, only needed when using pipelined models

Run the agent:

```shell
python3 agent.py dev
```

Now, your worker is running, and waiting for dispatches in order to make outbound calls.

### Making a call

You can dispatch an agent to make a call by using the `lk` CLI:

```shell
lk dispatch create \
  --new-room \
  --agent-name outbound-caller \
  --metadata '{"phone_number": "+1234567890", "transfer_to": "+9876543210"}'
```
