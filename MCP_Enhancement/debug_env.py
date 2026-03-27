import os

# 1. Define the path exactly as your config does
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

print(f"📂 Checking file at: {env_path}")

if not os.path.exists(env_path):
    print("❌ ERROR: File does not exist!")
else:
    print("✅ File found. Reading contents...")
    with open(env_path, 'r') as f:
        lines = f.readlines()

    found = False
    for i, line in enumerate(lines):
        # Print line number and the first few chars of the key to debug
        clean_line = line.strip()
        print(f"   Line {i + 1}: {clean_line}")

        if clean_line.startswith("PINECONE_API_KEY"):
            found = True
            print("   🎉 FOUND IT! ^^^")

    if not found:
        print("\n❌ CRITICAL: 'PINECONE_API_KEY' was NOT found in the file.")
        print("   Please check for typos or ensure it is on its own line.")