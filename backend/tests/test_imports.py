"""Test if all imports work."""

print("Testing imports...")

try:
    from app.config import settings
    print("✅ config imported")
except Exception as e:
    print(f"❌ config failed: {e}")

try:
    from app.models.state import TruthCheckState, Study
    print("✅ state models imported")
except Exception as e:
    print(f"❌ state models failed: {e}")

try:
    from app.tools.pubmed import PubMedTool
    print("✅ pubmed tool imported")
except Exception as e:
    print(f"❌ pubmed tool failed: {e}")

try:
    from langchain_anthropic import ChatAnthropic
    print("✅ langchain_anthropic imported")
except Exception as e:
    print(f"❌ langchain_anthropic failed: {e}")

try:
    from app.agents.search_agent import SearchAgent
    print("✅ search_agent imported")
except Exception as e:
    print(f"❌ search_agent failed: {e}")

print("\n✅ All imports successful!")
