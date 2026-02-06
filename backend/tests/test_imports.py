"""Test if all imports work."""

print("Testing imports...")

try:
    print("✅ config imported")
except Exception as e:
    print(f"❌ config failed: {e}")

try:
    print("✅ state models imported")
except Exception as e:
    print(f"❌ state models failed: {e}")

try:
    print("✅ pubmed tool imported")
except Exception as e:
    print(f"❌ pubmed tool failed: {e}")

try:
    print("✅ langchain_groq imported")
except Exception as e:
    print(f"❌ langchain_groq failed: {e}")

try:
    print("✅ search_agent imported")
except Exception as e:
    print(f"❌ search_agent failed: {e}")

print("\n✅ All imports successful!")
