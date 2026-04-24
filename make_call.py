"""
Script to trigger an outbound call via LiveKit agent dispatch.

This script dispatches a job to the LiveKit agent, which will then
make an outbound call to the specified number.
"""

import os
import json
import asyncio
from dotenv import load_dotenv
from livekit import api

# Load environment variables
load_dotenv(dotenv_path=".env.local")


async def dispatch_outbound_call(phone_number: str, transfer_number: str | None = None):
    """
    Dispatch an outbound call job to the LiveKit agent.

    Args:
        phone_number: Phone number to call (E.164 format, e.g., +19415180701)
        transfer_number: Phone number for transferring to human agent (optional)
    """
    # Get LiveKit credentials from environment
    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not all([url, api_key, api_secret]):
        raise ValueError("Missing LiveKit credentials in .env.local")

    # Default transfer number to Twilio phone if not provided
    if not transfer_number:
        transfer_number = os.getenv("MAX_PHONE_NUMBER", "+19412314887")

    # Create the metadata with call information
    metadata = json.dumps({
        "phone_number": phone_number,
        "transfer_to": transfer_number
    })

    print(f"Dispatching outbound call to {phone_number}...")
    print(f"Transfer number: {transfer_number}")
    print(f"Metadata: {metadata}")

    # Create LiveKit API client
    lk_api = api.LiveKitAPI(
        url=url,
        api_key=api_key,
        api_secret=api_secret,
    )

    # Dispatch the job to the agent
    # This creates a room and dispatches the job to a worker
    dispatch = await lk_api.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name="outbound-caller",  # Must match agent_name in agent.py
            room="outbound-call-" + phone_number.replace("+", ""),  # Unique room name
            metadata=metadata,
        )
    )

    print(f"\n✓ Call dispatched successfully!")
    print(f"  Dispatch ID: {dispatch.id}")
    print(f"  Room: {dispatch.room}")
    print(f"  Agent: {dispatch.agent_name}")
    print(f"\nThe agent will now call {phone_number}...")
    print("Check the agent logs for call progress.")

    await lk_api.aclose()


if __name__ == "__main__":
    # Get phone number from environment or use default
    phone_to_call = os.getenv("TWILIO_TO_NUMBER", "+19415180701")

    print(f"\n{'='*60}")
    print("LiveKit Outbound Caller - Make Call")
    print(f"{'='*60}\n")

    # Run the dispatch
    asyncio.run(dispatch_outbound_call(phone_to_call))
