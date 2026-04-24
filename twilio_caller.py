"""Twilio Outbound Caller Script"""
import os
from dotenv import load_dotenv
from twilio.rest import Client

# Load environment variables from .env.local
load_dotenv(dotenv_path=".env.local")


def make_call(to_number: str, from_number: str = None, twiml_url: str = None):
    """
    Make an outbound call using Twilio

    Args:
        to_number: Phone number to call (E.164 format, e.g., +19413230041)
        from_number: Your Twilio phone number (optional, uses env var if not provided)
        twiml_url: URL with TwiML instructions (optional, uses default demo if not provided)

    Returns:
        Call SID if successful
    """
    # Get credentials from environment variables
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    if not account_sid or not auth_token:
        raise ValueError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in .env.local")

    # Use environment variable for from_number if not provided
    if not from_number:
        from_number = os.getenv("TWILIO_PHONE_NUMBER")
        if not from_number:
            raise ValueError("TWILIO_PHONE_NUMBER must be set in .env.local or passed as argument")

    # Use default demo TwiML if not provided
    if not twiml_url:
        twiml_url = "http://demo.twilio.com/docs/voice.xml"

    # Initialize Twilio client
    client = Client(account_sid, auth_token)

    # Make the call
    call = client.calls.create(
        url=twiml_url,
        to=to_number,
        from_=from_number
    )

    print(f"Call initiated successfully!")
    print(f"Call SID: {call.sid}")
    print(f"Status: {call.status}")

    return call.sid


if __name__ == "__main__":
    # Example usage
    try:
        # Make a call to the specified number
        to = os.getenv("TWILIO_TO_NUMBER", "+19413230041")
        make_call(to_number=to)
    except Exception as e:
        print(f"Error making call: {e}")
