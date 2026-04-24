"""
AI Outbound Caller Agent

This agent makes automated phone calls using LiveKit's real-time communication platform.
It uses OpenAI's Realtime API for speech-to-speech communication, providing a natural
conversational experience for appointment confirmations and call management.

Key Features:
- Automated appointment confirmation calls
- Call transfer functionality to human agents
- Voicemail detection
- Appointment scheduling assistance
- Natural voice conversation using OpenAI's Realtime API

Architecture:
- Uses SIP (Session Initiation Protocol) for phone connectivity
- LiveKit for real-time audio streaming
- OpenAI Realtime API for speech-to-speech processing
- Function calling for agent actions (transfer, hangup, etc.)

Note: This agent requires a Unix-like environment (Linux/macOS/WSL2) due to
LiveKit's IPC system requirements. It will not work on Windows/MINGW64.
"""

from __future__ import annotations

import os
import asyncio
import logging
from dotenv import load_dotenv
import json
from typing import Any

# LiveKit core imports for real-time communication and API access
from livekit import rtc, api

# LiveKit agents framework for building voice agents
from livekit.agents import (
    AgentSession,  # Manages the conversation session
    Agent,  # Base class for creating agents
    JobContext,  # Provides context about the current job/call
    function_tool,  # Decorator for creating callable functions
    RunContext,  # Context during function execution
    get_job_context,  # Access to current job context
    cli,  # Command-line interface utilities
    WorkerOptions,  # Configuration for the worker
    RoomInputOptions,  # Configuration for room audio input
)

# LiveKit plugins for various AI services
from livekit.plugins import (
    anthropic,  # Claude AI (Primary LLM)
    deepgram,   # Speech-to-text
    cartesia,   # Text-to-speech
    silero,     # Voice activity detection
    noise_cancellation,  # Background noise removal
    openai,     # OpenAI Realtime API (works without inference executor)
)
# from livekit.plugins.turn_detector.english import EnglishModel  # Turn detection - causes WSL2 timeout

# Load environment variables from .env.local file
# This includes API keys, LiveKit credentials, and SIP trunk configuration
load_dotenv(dotenv_path=".env.local")

# Configure logging for the agent
logger = logging.getLogger("outbound-caller")
logger.setLevel(logging.INFO)

# SIP trunk ID for making outbound calls via LiveKit
# This is configured in your LiveKit dashboard and connects to Twilio
outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")


class OutboundCaller(Agent):
    """
    Outbound calling agent for appointment confirmations.

    This agent handles automated phone calls to confirm appointments,
    provide scheduling assistance, and transfer calls to human agents when needed.

    Attributes:
        participant: The remote participant (person being called) in the conversation
        dial_info: Dictionary containing phone numbers and transfer information
    """

    def __init__(
        self,
        *,
        name: str,
        appointment_time: str,
        dial_info: dict[str, Any],
    ):
        """
        Initialize the outbound caller agent.

        Args:
            name: The customer's name for personalization
            appointment_time: The scheduled appointment time to confirm
            dial_info: Dictionary with 'phone_number' and 'transfer_to' keys
        """
        super().__init__(
            instructions=f"""
            You are John, a sharp and persistent health insurance sales agent. Your interface with users will be voice.
            You are a professional closer who doesn't take no for an answer - your job is to get them to agree to a FREE QUOTE.

            CRITICAL OPENING SCRIPT - FOLLOW EXACTLY:

            1. GREETING (enthusiastic and confident):
            "Hey! This is John. How's it going with you today?"

            2. WAIT FOR THEIR RESPONSE - Let them answer

            3. REASON FOR CALL (after they respond):
            "The reason for the call today {name} is that I work with lots of individuals who are self-employed, small business owners who either pay a lot or are unhappy with their health insurance. I was just seeing if that was the case with you?"

            YOUR GOAL: Get them to agree to a FREE quote. That's it. Not to sell them, just get them to see what's available.

            KEY SELLING POINTS (use these naturally in conversation):
            - We save individuals and families around twenty to forty percent on their monthly premium with HIGHER caliber coverage
            - The plan is twenty to forty percent more affordable than anything else out there
            - Our job is to keep your insurance company honest
            - We make health insurance more affordable than anything you see online
            - We keep their current insurance company honest by showing them what else is out there
            - It's completely free to get a quote - no obligation whatsoever
            - Most people don't realize they're overpaying until they compare
            - Takes literally 2 minutes to see if we can save them money

            AGE VERIFICATION - IMPORTANT FOR ACCURATE QUOTES:
            Before closing, ask their age to qualify the premium:
            "Real quick {name}, just so Max can pull up the right plans for you - what's your age? This helps us make sure we're showing you the most accurate pricing."

            [Wait for age response]

            CLOSING LINE - USE THIS TO GET AGREEMENT:
            After getting their age and handling objections, use this closing:
            "Perfect! Look {name}, the plan is twenty to forty percent more affordable than anything else out there, and our job is to keep your insurance company honest and make health insurance more affordable than anything you see online. With that being said, would it be okay to get you over to Max, my health insurance specialist?"

            WHEN THEY AGREE:
            Say: "Perfect! I'm going to get you over to my top agent Max who would be more than happy to assist. One second."
            Then immediately use the transfer_call tool.

            HANDLING OBJECTIONS - BE PERSISTENT AND SHARP:

            "I'm happy with my plan":
            → "That's great {name}! But when's the last time you actually compared? Most people say they're happy until they realize they're overpaying by two hundred to four hundred dollars a month. What if I could show you the same coverage or better for twenty to forty percent less? Would you at least want to see the numbers?"

            "I don't have time":
            → "I totally get it {name}, but that's exactly why I'm calling. Takes literally 2 minutes to run the quote. What's it hurt to at least SEE if you're overpaying? If you're already getting the best deal, great - you'll know for sure. But what if you're not?"

            "Not interested":
            → "I hear you {name}, but can I ask - are you saying you're not interested in potentially saving two hundred, three hundred, four hundred dollars a month on your health insurance? Because that's what we're averaging with our clients. It's free to check - what's the worst that happens, you find out you already have a good deal?"

            "I need to think about it":
            → "Absolutely {name}, I respect that. But think about what? It's a free quote - there's nothing to think about. Let's just run the numbers real quick, see what's available, and THEN you can think about it with actual information instead of guessing. Fair enough?"

            "How did you get my number?":
            → "We work with self-employed folks and small business owners specifically {name}. Are you self-employed or have your own business? [Wait for answer] Perfect, that's exactly who we help save the most money."

            "I can't afford to switch":
            → "Wait, hold on {name} - switching is FREE. There's zero cost to switch health insurance. And if we can show you BETTER coverage for LESS money, wouldn't that actually help you afford it better? That's literally the whole point of what I do."

            "Send me information":
            → "I could {name}, but here's the thing - you'll get an email, you'll ignore it, and you'll keep overpaying. Why not take 2 minutes right now while I have you? My agent Max can run your quote in real-time and you'll know immediately if we can save you money. What's your current monthly premium?"

            "Call me back later":
            → "I can {name}, but be honest - you're not going to answer when I call back, right? We both know how that goes. You're on the phone with me RIGHT NOW. Let's just get you the quote, and if it doesn't make sense, we never talk again. But if it DOES make sense, you could be saving hundreds of dollars a month. Why wait?"

            "I'm not the decision maker":
            → "I totally understand {name}. So who handles the health insurance in your family? [Get name] Okay perfect. Here's what I'll do - let me get you the quote anyway so you have the information. Then you can show [spouse name] the numbers. If they see we can save you twenty to forty percent, I bet they'll be interested. Sound good?"

            "I'm on the Do Not Call list":
            → "I understand {name}. We scrub on the DNC list, so if your phone number was on the national DO NOT CALL REGISTRY, we wouldn't have dialed you. But I respect that - one more thing though, would you be open to just hearing about how we can save you twenty to forty percent on better coverage?"

            [If they say NO again]
            → "I completely understand {name}. I appreciate your time today. You have a great rest of your day." Then use the end_call tool.

            "I already shopped around":
            → "That's awesome {name}! When did you shop around? [Get timeframe] Okay, so here's the thing - rates change constantly. What was available 6 months ago, a year ago, is totally different now. Plus we have access to plans most people don't even know exist. What's it hurt to compare one more time, especially if we can beat what you found?"

            "Remove me from your list":
            → "I can do that {name}, absolutely. But real quick before I do - can I ask, are you saying you don't want to save twenty to forty percent on your health insurance with better coverage? Because that seems like it would be worth 2 minutes of your time. If after the quote you still want off the list, no problem. But at least see the numbers first?"

            CONVERSATION STYLE - SALES PROFESSIONAL:
            - Confident, direct, and persistent - you're helping them save money
            - Use their name frequently - builds rapport
            - Don't accept "no" easily - every objection has a counter
            - Assume the sale - talk like they're already getting the quote
            - Create urgency - "while I have you", "let's do it right now"
            - Use social proof - "most people", "our clients average"
            - Focus on THEIR money being wasted, not your product
            - Turn objections into questions that make them think
            - Use "but" to pivot objections: "I hear you, BUT..."

            CRITICAL RULES:
            1. Your ONLY job is to get them to agree to a FREE quote
            2. When they agree, immediately say the transfer line and use transfer_call
            3. NEVER give up after one objection - try at least 2-3 times with different angles
            4. Keep reframing - it's not about selling insurance, it's about saving THEIR money
            5. Make it easy - "just 2 minutes", "free quote", "no obligation"
            6. If they're truly aggressive or hostile, politely end the call
            7. Always be professional - pushy but never rude

            GUARDRAILS - STAY ON TRACK:

            ✅ YOU CAN DISCUSS (Keep it general):
            - Health insurance in general terms (costs too high, people overpaying, etc.)
            - The problem with current insurance (expensive, bad coverage)
            - twenty to forty percent savings and better coverage (general benefits)
            - Basic small talk: "How are you?", weather, casual conversation
            - Your location if asked: "I'm in Tampa, FL - been here for 20 years"

            ❌ REDIRECT TO MAX (These are too detailed for you):
            - Specific plan details (HMO, PPO, deductibles, copays, networks)
            - Exact prices or premiums (beyond "twenty to forty percent savings")
            - Medical coverage specifics (prescriptions, doctors, procedures)
            - How to enroll, paperwork, application process
            - Policy comparisons or recommendations

            🔄 OFF-TOPIC? REDIRECT BACK:
            If they ask about anything NOT related to insurance (sports, politics, personal life beyond basic pleasantries):
            → Answer briefly and politely, then pivot back: "But hey, real quick {name}, back to what I was saying about the free quote..."
            → Keep it short and redirect to insurance

            📍 LOCATION RESPONSE:
            If asked "Where are you calling from?" or "Where are you located?":
            → "I'm in Tampa, FL - been here for 20 years. Love it here!"

            ✅ WHEN THEY ASK DETAILED QUESTIONS, USE THESE:
            - "That's exactly what Max will go over with you on the free quote"
            - "Max is the expert on all the plan details - let me get you over to him"
            - "Great question! Max will walk you through all of that. Let's get you connected"
            - "I don't want to give you wrong information - Max handles all the specifics"

            YOUR MAIN JOB:
            ✅ Get them to agree to a FREE quote
            ✅ Handle objections about getting the quote
            ✅ Transfer to Max when they agree

            Remember: You're John from Tampa, FL (20 years). You're friendly and conversational about insurance problems, but Max is the expert on specifics.
            The person you're calling is named {name} - use their name to build rapport.
            Transfer to Max (your top agent) when they agree.
            """
        )
        # Keep reference to the participant for call operations (transfers, hangups, etc.)
        self.participant: rtc.RemoteParticipant | None = None

        # Store dial information (phone numbers, transfer destination)
        self.dial_info = dial_info

    def set_participant(self, participant: rtc.RemoteParticipant):
        """
        Set the participant reference after they join the call.

        Args:
            participant: The remote participant who answered the call
        """
        self.participant = participant

    async def hangup(self):
        """
        End the call by deleting the LiveKit room.

        This terminates the call and cleans up all connections.
        The room deletion triggers automatic disconnection of all participants.
        """
        job_ctx = get_job_context()
        await job_ctx.api.room.delete_room(
            api.DeleteRoomRequest(
                room=job_ctx.room.name,
            )
        )

    @function_tool()
    async def transfer_call(self, ctx: RunContext):
        """
        Transfer the call to Max (top agent) when prospect agrees to get a quote.

        Use this IMMEDIATELY when the prospect agrees.
        The instructions already told them: "Perfect! I'm going to get you over to my top agent Max..."

        Args:
            ctx: Runtime context with access to the session and agent state

        Returns:
            str: Status message ("cannot transfer call" if no transfer number configured)
        """
        transfer_to = self.dial_info["transfer_to"]
        if not transfer_to:
            return "cannot transfer call"

        logger.info(f"transferring call to Max at {transfer_to}")

        # Transfer immediately - John already said the transfer line in the instructions
        job_ctx = get_job_context()
        try:
            # Use LiveKit SIP API to transfer the call to Max's phone number
            await job_ctx.api.sip.transfer_sip_participant(
                api.TransferSIPParticipantRequest(
                    room_name=job_ctx.room.name,
                    participant_identity=self.participant.identity,
                    transfer_to=f"tel:{transfer_to}",
                )
            )

            logger.info(f"transferred call to Max successfully")
        except Exception as e:
            logger.error(f"error transferring call: {e}")
            # Apologize for technical issue
            await ctx.session.generate_reply(
                instructions="apologize that there's a technical issue and you'll call them right back with Max"
            )
            await self.hangup()

    @function_tool()
    async def end_call(self, ctx: RunContext):
        """
        End the call when the user is ready to hang up.

        This tool is called by the AI when the conversation has concluded.
        It ensures the agent finishes speaking before disconnecting.

        Args:
            ctx: Runtime context with access to the session
        """
        logger.info(f"ending the call for {self.participant.identity}")

        # Wait for the agent to finish speaking current message before hanging up
        current_speech = ctx.session.current_speech
        if current_speech:
            await current_speech.wait_for_playout()

        await self.hangup()

    @function_tool()
    async def look_up_availability(
        self,
        ctx: RunContext,
        date: str,
    ):
        """
        Look up available appointment times for rescheduling.

        This is a placeholder function that simulates checking a scheduling system.
        In production, this would query your actual appointment database.

        Args:
            ctx: Runtime context
            date: The date to check availability for (in natural language)

        Returns:
            dict: Available appointment times
        """
        logger.info(
            f"looking up availability for {self.participant.identity} on {date}"
        )
        # Simulate database lookup delay
        await asyncio.sleep(3)
        # Return mock availability data - replace with real database query
        return {
            "available_times": ["1pm", "2pm", "3pm"],
        }

    @function_tool()
    async def confirm_appointment(
        self,
        ctx: RunContext,
        date: str,
        time: str,
    ):
        """
        Confirm an appointment for a specific date and time.

        This tool is called when the user confirms or reschedules their appointment.
        In production, this would update your scheduling system.

        Args:
            ctx: Runtime context
            date: The appointment date
            time: The appointment time

        Returns:
            str: Confirmation message
        """
        logger.info(
            f"confirming appointment for {self.participant.identity} on {date} at {time}"
        )
        # In production: Update your scheduling database here
        return "reservation confirmed"

    @function_tool()
    async def detected_answering_machine(self, ctx: RunContext):
        """
        Handle voicemail detection.

        This tool is called by the AI when it detects that the call reached voicemail
        instead of a live person. The agent should call this AFTER hearing the voicemail greeting.

        Args:
            ctx: Runtime context
        """
        logger.info(f"detected answering machine for {self.participant.identity}")
        # End the call immediately when voicemail is detected
        await self.hangup()


async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for handling outbound calls.

    This function is called by the LiveKit agents framework when a new job (call)
    is dispatched. It sets up the call, initializes the AI agent, and manages the
    complete call lifecycle from dialing to completion.

    Workflow:
    1. Connect to the LiveKit room
    2. Parse call metadata (phone number, transfer info)
    3. Create and configure the AI agent
    4. Set up the session with OpenAI Realtime API
    5. Start the session (begins loading models)
    6. Dial the phone number via SIP
    7. Wait for the user to answer
    8. Connect the participant to the agent
    9. Let the conversation run until completion

    Args:
        ctx: Job context providing access to room, API, and job metadata
    """
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect()

    # Parse metadata passed during dispatch containing call information
    # dial_info structure:
    # {
    #     "phone_number": "+1234567890",  # Number to call
    #     "transfer_to": "+0987654321"    # Human agent number for transfers
    # }
    dial_info = json.loads(ctx.job.metadata)
    participant_identity = phone_number = dial_info["phone_number"]

    # Create the agent with personalized information
    # In production, you would look up customer details from your database
    agent = OutboundCaller(
        name="Jayden",  # TODO: Replace with database lookup
        appointment_time="",  # Not used for health insurance calls
        dial_info=dial_info,
    )

    # Configure the session using Claude Sonnet 4 with Deepgram STT and Cartesia TTS
    # This provides superior reasoning and natural conversation using the pipelined approach
    # Voice: Cartesia provides natural-sounding male voice optimized for health insurance discussions
    #     session = AgentSession(
    #         turn_detection=EnglishModel(),  # Detects when user finishes speaking
    #         vad=silero.VAD.load(),  # Voice activity detection for better turn-taking
    #         stt=deepgram.STT(),  # Deepgram speech-to-text (fast and accurate)
    #         tts=cartesia.TTS(voice="228fca29-3a0a-435c-8728-5cb483251068"),  # Your selected Cartesia voice
    #         llm=anthropic.LLM(model="claude-sonnet-4-20250514"),  # Claude Sonnet 4 (best reasoning)
    #     )

    # Using Claude with pipelined approach - WITHOUT turn_detection to avoid WSL2 timeout
    session = AgentSession(
        # turn_detection=EnglishModel(),  # DISABLED - causes WSL2 inference executor timeout
        vad=silero.VAD.load(
            min_silence_duration=0.3,  # Reduced from default 0.5 - faster response
            activation_threshold=0.4,  # Lower threshold - more sensitive to speech
        ),
        stt=deepgram.STT(),  # Deepgram speech-to-text
        tts=cartesia.TTS(voice="228fca29-3a0a-435c-8728-5cb483251068"),  # Your selected voice
        llm=anthropic.LLM(model="claude-sonnet-4-20250514"),  # Claude Sonnet 4
    )

    # OpenAI fallback if Claude doesn't work:
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="echo", temperature=0.8),
    # )

    # Start the session before dialing to ensure the agent is ready when the user answers
    # This prevents missing the first few seconds of what the user says
    session_started = asyncio.create_task(
        session.start(
            agent=agent,
            room=ctx.room,
            room_input_options=RoomInputOptions(
                # Enable Krisp noise cancellation optimized for telephony
                # This removes background noise for clearer conversations
                noise_cancellation=noise_cancellation.BVCTelephony(),
            ),
        )
    )

    # Initiate the outbound call via SIP trunk
    # This dials the phone number and waits for the user to answer
    try:
        await ctx.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=ctx.room.name,
                sip_trunk_id=outbound_trunk_id,  # Configured SIP trunk ID
                sip_call_to=phone_number,  # Number to dial
                participant_identity=participant_identity,  # Unique identifier
                wait_until_answered=True,  # Block until call is answered or fails
            )
        )

        # Wait for both the session to finish starting and the participant to join
        await session_started
        participant = await ctx.wait_for_participant(identity=participant_identity)
        logger.info(f"participant joined: {participant.identity}")

        # Give the agent a reference to the participant for call operations
        agent.set_participant(participant)

        # Conversation now runs automatically until:
        # - User hangs up
        # - Agent calls end_call() or hangup()
        # - Error occurs

    except api.TwirpError as e:
        # Handle SIP errors (busy, no answer, invalid number, etc.)
        logger.error(
            f"error creating SIP participant: {e.message}, "
            f"SIP status: {e.metadata.get('sip_status_code')} "
            f"{e.metadata.get('sip_status')}"
        )
        ctx.shutdown()


if __name__ == "__main__":
    # Start the LiveKit agents worker
    # This runs continuously, waiting for jobs to be dispatched
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,  # Function to call for each job
            agent_name="outbound-caller",  # Name used when dispatching jobs
        )
    )
