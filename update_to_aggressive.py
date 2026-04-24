# Update script to change agent to aggressive sales version
import shutil

# Backup current agent
shutil.copy("agent.py", "agent.py.backup-health-insurance")
print("✓ Backed up current agent.py")

# Read the aggressive sales script
aggressive_script = open("agent_aggressive_template.txt").read()

# Write it to agent.py
with open("agent.py", "w") as f:
    f.write(aggressive_script)

print("✓ Updated agent.py with aggressive sales script!")
print("\nNext steps:")
print("1. Delete cloud agent: lk agent delete --id CA_au4RYoVknRyg")
print("2. Restart local agent: python agent.py start")
print("3. Make test call: python make_call.py")
