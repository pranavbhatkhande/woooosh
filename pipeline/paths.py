from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
PROMPT_DIR = DATA_DIR / "prompts"
CACHE_DIR = ROOT / "pipeline" / ".cache"
OUT_DIR = ROOT / "pipeline" / "out"
OUT_PROMPTS = OUT_DIR / "prompts"
CURATED_PATH = ROOT / "pipeline" / "curated" / "prompts.txt"
SPARKQL_CACHE = CACHE_DIR / "sparql"
LLM_CACHE = CACHE_DIR / "llm"
WIKI_CACHE = CACHE_DIR / "wiki"
PAGEVIEW_CACHE = CACHE_DIR / "pageviews"
