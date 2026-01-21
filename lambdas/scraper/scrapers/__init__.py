"""
Simple registry mapping company names to scrape functions.
"""

from typing import List, Dict, Callable

from .anthropic import scrape_anthropic
from .openai import scrape_openai
from .deepmind import scrape_deepmind
from .xai import scrape_xai
from .jane_street import scrape_jane_street
from .citadel import scrape_citadel
from .two_sigma import scrape_two_sigma
from .point72 import scrape_point72
from .renaissance import scrape_rentech
from .ssi import scrape_ssi
from .thinking_machines import scrape_thinking_machines
from .perplexity import scrape_perplexity
from .mistral import scrape_mistral
from .meta import scrape_meta
from .google import scrape_google
from .apple import scrape_apple
from .microsoft import scrape_microsoft
from .amazon import scrape_amazon
from .nvidia import scrape_nvidia
from .netflix import scrape_netflix
from .reddit import scrape_reddit
from .spotify import scrape_spotify
from .tiktok import scrape_tiktok
from .uber import scrape_uber
from .waymo import scrape_waymo
from .figureai import scrape_figureai
from .togetherai import scrape_togetherai
from .huggingface import scrape_huggingface
from .cohere import scrape_cohere
from .reflectionai import scrape_reflectionai
from .jump import scrape_jump
from .hrt import scrape_hrt
from .imc import scrape_imc
from .drw import scrape_drw
from .tower import scrape_tower
from .optiver import scrape_optiver
from .deshaw import scrape_deshaw
from .xtx import scrape_xtx


SCRAPERS: Dict[str, Callable[[str], List[Dict[str, str]]]] = {
    'Anthropic': scrape_anthropic,
    'OpenAI': scrape_openai,
    'Deepmind': scrape_deepmind,
    'xAI': scrape_xai,
    'Jane Street': scrape_jane_street,
    'Citadel': scrape_citadel,
    'Two Sigma': scrape_two_sigma,
    'Point72': scrape_point72,
    'Renaissance Technologies': scrape_rentech,
    'SSI': scrape_ssi,
    'Thinking Machines': scrape_thinking_machines,
    'Perplexity': scrape_perplexity,
    'Mistral': scrape_mistral,
    'Meta': scrape_meta,
    'Google': scrape_google,
    'Apple': scrape_apple,
    'Microsoft': scrape_microsoft,
    'Amazon': scrape_amazon,
    'Nvidia': scrape_nvidia,
    'Netflix': scrape_netflix,
    'Reddit': scrape_reddit,
    'Spotify': scrape_spotify,
    'Tiktok': scrape_tiktok,
    'Uber': scrape_uber,
    'Waymo': scrape_waymo,
    'FigureAI': scrape_figureai,
    'TogetherAI': scrape_togetherai,
    'HuggingFace': scrape_huggingface,
    'Cohere': scrape_cohere,
    'Reflection AI': scrape_reflectionai,
    'Jump': scrape_jump,
    'HRT': scrape_hrt,
    'IMC': scrape_imc,
    'DRW': scrape_drw,
    'Tower': scrape_tower,
    'Optiver': scrape_optiver,
    'DE Shaw': scrape_deshaw,
    'XTX': scrape_xtx,
}


def get_scraper(company_name: str) -> Callable[[str], List[Dict[str, str]]]:
    """Get scrape function for a company. Raises ValueError if not found."""
    if company_name not in SCRAPERS:
        raise ValueError(f"No scraper for '{company_name}'")
    return SCRAPERS[company_name]


def has_scraper(company_name: str) -> bool:
    """Check if scraper exists for company."""
    return company_name in SCRAPERS