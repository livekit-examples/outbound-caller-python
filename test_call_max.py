"""Quick test call to Max's number"""
import asyncio
from make_call import dispatch_outbound_call

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Test Call to Max: +19415180701")
    print("="*60 + "\n")
    
    # Call Max's number, transfer back to Max (same number for testing)
    asyncio.run(dispatch_outbound_call(
        phone_number="+19415180701",
        transfer_number="+19415180701"
    ))
