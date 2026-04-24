# Agent Customization Guide

## Quick Reference: Where to Make Changes

### 1. Change Voice (agent.py Line 342)

```python
tts=cartesia.TTS(voice="YOUR_VOICE_ID_HERE"),
```

**Popular Cartesia Voice IDs:**

**Male Voices:**

- `79f8b5fb-2cc8-479a-80df-29f7a7cf1a3e` - British Narration Man (professional, authoritative)
- `694f9389-aac1-45b6-b726-9d9369183238` - Friendly Guy (warm, conversational, American)
- `a0e99841-438c-4a64-b679-ae501e7d6091` - Confident British Man
- `63ff761f-c1e8-414b-b969-d1833d1c870c` - Pilot (calm, clear)

**Female Voices:**

- `95856005-0332-41b0-935f-352e296aa0df` - Professional Woman
- `638efaaa-4d0c-442e-b701-3fae16a90097` - Calm Woman
- `421b3369-f63f-4b03-8980-37a44df1d4e8` - News Lady (clear, professional)
- `f9836c6e-a0bd-460e-9d3c-f7299fa60f94` - Friendly Reading Lady

**To find more voices:**
Visit <https://play.cartesia.ai/library> and click on voices to get their IDs.

---

### 2. Change Personality/Instructions (agent.py Lines 106-125)

This section controls everything the agent says and how it behaves.

#### Example: Simple friendly caller

```python
instructions=f"""
You are a friendly and helpful assistant calling to check in with clients.
Your interface with users will be voice.

Keep your responses brief and natural. Speak like a real person, not a robot.
Be warm and personable. The client's name is {name}.

Your goal is to have a pleasant conversation and answer any questions they may have.
"""
```

#### Example: Professional appointment reminder

```python
instructions=f"""
You are calling to confirm an appointment.
Your interface with users will be voice.

You are professional, efficient, and friendly.
Keep the call brief - your goal is to:
1. Greet the client by name ({name})
2. Confirm they have an appointment at {appointment_time}
3. Ask if they can still make it
4. Thank them and end the call

Be polite but don't waste their time with unnecessary chit-chat.
"""
```

---

### 3. Change What Agent Says First

The agent automatically starts speaking based on its instructions. To control the opening:

**Add an initial greeting to the instructions:**

```python
instructions=f"""
You are a health insurance specialist calling clients.

IMPORTANT: When the call connects, immediately greet them by saying:
"Hi {name}, this is [Your Company] calling about your health insurance options. Do you have a minute to chat?"

Then wait for their response before continuing.
...
"""
```

---

### 4. Adjust Turn Detection Sensitivity (agent.py Line 339)

If the agent interrupts too much or waits too long:

```python
# More sensitive (agent speaks faster after user pauses)
turn_detection=EnglishModel(detection_threshold=0.6),

# Less sensitive (agent waits longer before speaking)
turn_detection=EnglishModel(detection_threshold=0.8),

# Default (currently used)
turn_detection=EnglishModel(),  # threshold=0.7
```

---

### 5. Client Name and Info (agent.py Line 330)

Currently hardcoded:

```python
agent = OutboundCaller(
    name="Jayden",  # Change this or look up from database
    appointment_time="",  # Add appointment time if needed
    dial_info=dial_info,
)
```

---

## Making Changes

**After editing agent.py:**

1. Save the file
2. Restart the local agent:

```bash
# Kill the current agent (Ctrl+C in the terminal where it's running)
# OR if running in background:
pkill -f "python agent.py"

# Start it again
python agent.py start
```

3. Make a test call:

```bash
python make_call.py
```

---

## Common Customizations

### Make voice warmer and more casual

- Use voice: `694f9389-aac1-45b6-b726-9d9369183238` (Friendly Guy)
- Instructions: "Be warm and casual, like talking to a friend"

### Make voice more professional

- Use voice: `79f8b5fb-2cc8-479a-80df-29f7a7cf1a3e` (British Narration Man)
- Instructions: "Be professional and courteous. Speak clearly and authoritatively"

### Reduce interruptions

- Increase turn detection threshold to 0.8
- Add to instructions: "Always let the user finish speaking completely before responding"

### Make agent speak first

- Add explicit opening to instructions as shown above

---

## Testing Tips

1. Make small changes one at a time
2. Test each change with a phone call
3. Check the agent logs to see what's happening
4. Iterate based on how the conversation feels

The agent is very flexible - experiment to find what works best for your use case!
