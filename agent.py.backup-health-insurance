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
# Attempt to disable inference executor BEFORE any other imports
# This is needed to avoid IPC timeout issues on Windows/WSL, though it may not
# fully work due to LiveKit framework limitations on Windows/MINGW64
os.environ["LIVEKIT_DISABLE_INFERENCE_EXECUTOR"] = "1"

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
)
from livekit.plugins.turn_detector.english import EnglishModel  # Turn detection

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
            You are a knowledgeable health insurance specialist with comprehensive expertise in the health insurance industry.
            Your interface with users will be voice. You are calling clients to discuss their health insurance options and answer questions.

            Your expertise includes:
            - All types of health insurance plans (HMO, PPO, EPO, POS, HDHP)
            - Medicare and Medicaid programs
            - Coverage options, deductibles, copays, and out-of-pocket maximums
            - Network providers and coverage limitations
            - Claims processes and dispute resolution
            - Healthcare reform and compliance (ACA, HIPAA)
            - Prescription drug coverage and formularies
            - Special enrollment periods and qualifying life events

            You speak with confidence and authority on health insurance matters. You are professional, patient, and able to explain
            complex insurance concepts in simple terms. Always ensure clients understand their options before making decisions.

            When the user would like to be transferred to a human agent, first confirm with them. Upon confirmation, use the transfer_call tool.
            The client's name is {name}.
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
        Transfer the call to a human agent after user confirmation.

        This function is called by the AI when the user requests to speak to a human.
        It uses SIP transfer to connect the call to a human agent's phone number.

        Args:
            ctx: Runtime context with access to the session and agent state

        Returns:
            str: Status message ("cannot transfer call" if no transfer number configured)
        """
        transfer_to = self.dial_info["transfer_to"]
        if not transfer_to:
            return "cannot transfer call"

        logger.info(f"transferring call to {transfer_to}")

        # Generate a confirmation message and let it play fully before transferring
        await ctx.session.generate_reply(
            instructions="let the user know you'll be transferring them"
        )

        job_ctx = get_job_context()
        try:
            # Use LiveKit SIP API to transfer the call to another phone number
            await job_ctx.api.sip.transfer_sip_participant(
                api.TransferSIPParticipantRequest(
                    room_name=job_ctx.room.name,
                    participant_identity=self.participant.identity,
                    transfer_to=f"tel:{transfer_to}",
                )
            )

            logger.info(f"transferred call to {transfer_to}")
        except Exception as e:
            logger.error(f"error transferring call: {e}")
            # Notify the user of the error and end the call
            await ctx.session.generate_reply(
                instructions="there was an error transferring the call."
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
    session = AgentSession(
        turn_detection=EnglishModel(),  # Detects when user finishes speaking
        vad=silero.VAD.load(),  # Voice activity detection for better turn-taking
        stt=deepgram.STT(),  # Deepgram speech-to-text (fast and accurate)
        tts=cartesia.TTS(voice="79f8b5fb-2cc8-479a-80df-29f7a7cf1a3e"),  # Cartesia British Narration Man
        llm=anthropic.LLM(model="claude-sonnet-4-20250514"),  # Claude Sonnet 4 (best reasoning)
    )

    # Alternative: OpenAI Realtime API (simpler but less powerful)
    # Uncomment below to switch back to OpenAI:
    #
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(
    #         voice="echo",
    #         temperature=0.8,
    #     ),
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
