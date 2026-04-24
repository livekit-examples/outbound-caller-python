"""
Create Inbound SIP Trunk Configuration

This script sets up the complete SIP trunk configuration for handling inbound calls
to your LiveKit agent. It creates both Twilio and LiveKit trunk configurations
and connects them together.

What it does:
1. Creates a Twilio SIP trunk that routes calls to LiveKit
2. Creates a LiveKit inbound SIP trunk for your phone number
3. Sets up a dispatch rule to route calls to agent rooms

Prerequisites:
- Twilio account with phone number
- LiveKit account with SIP configured
- lk CLI installed (LiveKit command-line tool)

Usage:
    python create_inbound_trunk.py

Environment Variables Required:
- TWILIO_ACCOUNT_SID: Your Twilio account SID
- TWILIO_AUTH_TOKEN: Your Twilio auth token
- TWILIO_PHONE_NUMBER: Your Twilio phone number
- LIVEKIT_SIP_URI: Your LiveKit SIP URI from dashboard
"""

import json
import logging
import os
import re
import subprocess
from dotenv import load_dotenv
from twilio.rest import Client


def get_env_var(var_name):
    """
    Get an environment variable or exit if not set.

    Args:
        var_name: Name of the environment variable

    Returns:
        str: The environment variable value

    Raises:
        SystemExit: If the variable is not set
    """
    value = os.getenv(var_name)
    if value is None:
        logging.error(f"Environment variable '{var_name}' not set.")
        exit(1)
    return value

def create_livekit_trunk(client, sip_uri):
    """
    Create a Twilio SIP trunk that routes calls to LiveKit.

    This creates a Twilio trunk with an origination URL pointing to your
    LiveKit SIP endpoint. This allows Twilio to forward incoming calls to
    your LiveKit agent.

    Args:
        client: Twilio client instance
        sip_uri: LiveKit SIP URI (e.g., sip:xxxxx.sip.livekit.cloud)

    Returns:
        Trunk: The created Twilio trunk object
    """
    # Generate a unique domain name for this trunk
    domain_name = f"livekit-trunk-{os.urandom(4).hex()}.pstn.twilio.com"

    # Create the SIP trunk in Twilio
    trunk = client.trunking.v1.trunks.create(
        friendly_name="LiveKit Trunk",
        domain_name=domain_name,
    )

    # Add LiveKit as the destination for calls from this trunk
    trunk.origination_urls.create(
        sip_url=sip_uri,
        weight=1,  # Priority weight
        priority=1,  # Routing priority
        enabled=True,
        friendly_name="LiveKit SIP URI",
    )

    logging.info("Created new LiveKit Trunk.")
    return trunk


def create_inbound_trunk(phone_number):
    """
    Create a LiveKit inbound SIP trunk for receiving calls.

    This uses the LiveKit CLI to create an inbound trunk that can receive
    calls from your Twilio phone number.

    Args:
        phone_number: Twilio phone number in E.164 format (e.g., +1234567890)

    Returns:
        str: The trunk SID, or None if creation failed
    """
    # Prepare trunk configuration
    trunk_data = {
        "trunk": {
            "name": "Inbound LiveKit Trunk",
            "numbers": [phone_number]
        }
    }

    # Write configuration to temporary file
    with open('inbound_trunk.json', 'w') as f:
        json.dump(trunk_data, f, indent=4)

    # Create trunk using LiveKit CLI
    result = subprocess.run(
        ['lk', 'sip', 'inbound', 'create', 'inbound_trunk.json'],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        logging.error(f"Error executing command: {result.stderr}")
        return None

    # Extract trunk SID from output (format: ST_xxxxx)
    match = re.search(r'ST_\w+', result.stdout)
    if match:
        inbound_trunk_sid = match.group(0)
        logging.info(f"Created inbound trunk with SID: {inbound_trunk_sid}")
        return inbound_trunk_sid
    else:
        logging.error("Could not find inbound trunk SID in output.")
        return None


def create_dispatch_rule(trunk_sid):
    """
    Create a dispatch rule for routing inbound calls.

    This rule determines how incoming calls are routed to agent rooms.
    Each call creates a new room with the prefix "call-".

    Args:
        trunk_sid: The inbound trunk SID to associate with this rule
    """
    # Configure dispatch rule
    dispatch_rule_data = {
        "name": "Inbound Dispatch Rule",
        "trunk_ids": [trunk_sid],
        "rule": {
            "dispatchRuleIndividual": {
                "roomPrefix": "call-"  # Each call gets a unique room: call-xxxxx
            }
        }
    }

    # Write configuration to temporary file
    with open('dispatch_rule.json', 'w') as f:
        json.dump(dispatch_rule_data, f, indent=4)

    # Create dispatch rule using LiveKit CLI
    result = subprocess.run(
        ['lk', 'sip', 'dispatch-rule', 'create', 'dispatch_rule.json'],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        logging.error(f"Error executing command: {result.stderr}")
        return

    logging.info(f"Dispatch rule created: {result.stdout}")


def main():
    """
    Main function to set up complete inbound SIP trunk configuration.

    This orchestrates the entire setup process:
    1. Load environment variables
    2. Create/verify Twilio trunk
    3. Create LiveKit inbound trunk
    4. Create dispatch rule

    The script is idempotent - if the Twilio trunk already exists, it will be reused.
    """
    # Load configuration from .env.local
    load_dotenv(dotenv_path=".env.local")
    logging.basicConfig(level=logging.INFO)

    # Get required credentials and configuration
    account_sid = get_env_var("TWILIO_ACCOUNT_SID")
    auth_token = get_env_var("TWILIO_AUTH_TOKEN")
    phone_number = get_env_var("TWILIO_PHONE_NUMBER")
    sip_uri = get_env_var("LIVEKIT_SIP_URI")

    # Initialize Twilio client
    client = Client(account_sid, auth_token)

    # Check if LiveKit trunk already exists in Twilio
    existing_trunks = client.trunking.v1.trunks.list()
    livekit_trunk = next(
        (trunk for trunk in existing_trunks if trunk.friendly_name == "LiveKit Trunk"),
        None
    )

    # Create trunk if it doesn't exist, otherwise reuse existing one
    if not livekit_trunk:
        livekit_trunk = create_livekit_trunk(client, sip_uri)
    else:
        logging.info("LiveKit Trunk already exists. Using the existing trunk.")

    # Create LiveKit inbound trunk for this phone number
    inbound_trunk_sid = create_inbound_trunk(phone_number)

    # If trunk creation succeeded, create dispatch rule
    if inbound_trunk_sid:
        create_dispatch_rule(inbound_trunk_sid)


if __name__ == "__main__":
    main()