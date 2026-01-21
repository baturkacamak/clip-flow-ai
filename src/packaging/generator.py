import instructor
from typing import List, Optional, Any
from pydantic import BaseModel
from openai import OpenAI
from anthropic import Anthropic
from loguru import logger
from src.config_manager import ConfigManager
from src.intelligence.models import ViralClip
from src.packaging.models import VideoPackage
from src.packaging.prompts import METADATA_SYSTEM_PROMPT, USER_METADATA_TEMPLATE

class MetadataResponse(BaseModel):
    title: str
    description: str
    tags: List[str]
    captions: str

class MetadataGenerator:
    def __init__(self, config_manager: ConfigManager):
        self.cfg = config_manager.intelligence
        self.pkg_cfg = config_manager.packaging
        self.client: Optional[Any] = self._init_client()

    def _init_client(self) -> Optional[Any]:
        if self.cfg.llm_provider == "openai":
            api_key = self.cfg.openai_api_key
            if not api_key:
                logger.warning("OpenAI API Key not found.")
                return None
            return instructor.from_openai(OpenAI(api_key=api_key))
        
        elif self.cfg.llm_provider == "anthropic":
            api_key = self.cfg.anthropic_api_key
            if not api_key:
                logger.warning("Anthropic API Key not found.")
                return None
            return instructor.from_anthropic(Anthropic(api_key=api_key))
        return None

    def generate_metadata(self, clip: ViralClip, video_path: str, thumbnail_path: str) -> VideoPackage:
        """Generates metadata using LLM."""
        default_pkg = VideoPackage(
            video_path=video_path,
            thumbnail_path=thumbnail_path,
            title=clip.title,
            description=f"Watch this {clip.category} clip! #shorts",
            tags=["#shorts", "#viral"],
            captions=clip.reasoning,
            platforms=["youtube", "tiktok"]
        )

        if not self.client:
            return default_pkg

        try:
            resp = self.client.chat.completions.create(
                model=self.cfg.model_name,
                response_model=MetadataResponse,
                messages=[
                    {"role": "system", "content": METADATA_SYSTEM_PROMPT},
                    {"role": "user", "content": USER_METADATA_TEMPLATE.format(
                        clip_title=clip.title,
                        clip_reasoning=clip.reasoning,
                        clip_category=clip.category
                    )}
                ],
                max_retries=2,
            )
            
            # Limit tags
            tags = resp.tags[:self.pkg_cfg.hashtags_count]
            
            return VideoPackage(
                video_path=video_path,
                thumbnail_path=thumbnail_path,
                title=resp.title,
                description=resp.description,
                tags=tags,
                captions=resp.captions,
                platforms=["youtube", "tiktok"]
            )

        except Exception as e:
            logger.error(f"Metadata generation failed: {e}")
            return default_pkg