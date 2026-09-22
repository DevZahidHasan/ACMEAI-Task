import logging
import sys
import os
from pydantic import ValidationError
from core.config import load_config
from core.detectors import SamMaskV1Detector
from core.api_client import ApiClient
from core.analyzer import FieldBoundaryAnalyzer
from synthetic_generator import generate_synthetic_video

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def main():
    config_path = os.getenv("CONFIG_PATH", "config.json")
    
    try:
        config = load_config(config_path)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except ValidationError as e:
        logger.error(f"Configuration validation failed:\n{e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {e}")
        sys.exit(1)

    if config.debug_mode:
        logging.getLogger().setLevel(logging.DEBUG)

    # Ensure the synthetic video exists
    if not os.path.exists(config.video_path):
        logger.info(f"Generating synthetic video: {config.video_path}")
        generate_synthetic_video(config.video_path)

    # Wire dependencies
    detector = SamMaskV1Detector(config.field_detector)
    api_client = ApiClient(config.api_url)
    
    analyzer = FieldBoundaryAnalyzer(config, detector, api_client)
    
    try:
        results = analyzer.process_video()
        logger.info(f"Pipeline executed successfully. Total results: {len(results)}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
