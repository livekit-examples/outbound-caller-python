"""
Test outbound call that transfers to Max
"""
import os
import json
import asyncio
from dotenv import load_dotenv
from livekit import api

load_dotenv(dotenv_path=".env.local")

async def test_call_with_transfer(phone_to_call: str, max_phone: str):
    """Test call that transfers to Max when prospect agrees."""
    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    metadata = json.dumps({
        "phone_number": phone_to_call,
        "transfer_to": max_phone  # Max's number for transfer
    })

    print(f"\n{'='*60}")
    print("TEST CALL - Transfer to Max")
    print(f"{'='*60}")
    print(f"\nCalling: {phone_to_call}")
    print(f"Will transfer to: {max_phone}")
    print(f"\nWhen John asks about health insurance, agree to the quote.")
    print(f"John will say: 'Perfect! I'm going to get you over to my top agent Max...'")
    print(f"Then he'll transfer you to Max at {max_phone}")
    print(f"{'='*60}\n")

    lk_api = api.LiveKitAPI(url=url, api_key=api_key, api_secret=api_secret)
    
    dispatch = await lk_api.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name="outbound-caller",
            room="test-call-" + phone_to_call.replace("+", ""),
            metadata=metadata,
        )
    )

    print(f"Call dispatched! Dispatch ID: {dispatch.id}")
    print(f"Check agent logs for progress...")
    
    await lk_api.aclose()

if __name__ == "__main__":
    # YOUR PHONE (will receive the call from John)
    your_phone = "+19415180701"
    
    # MAX'S PHONE (where call transfers when you agree to quote)
    max_phone = "+1XXXXXXXXXX"  # ← PUT MAX'S NUMBER HERE
    
    asyncio.run(test_call_with_transfer(your_phone, max_phone))
