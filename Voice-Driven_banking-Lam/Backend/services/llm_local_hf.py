import logging
import asyncio

import transformers
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

pipeline = None
# Pre-quantized GPTQ model for optimized inference
MODEL_ID = "TheBloke/Mistral-7B-Instruct-v0.2-GPTQ"

try:
    logger.info(f"Initializing pre-quantized pipeline for '{MODEL_ID}'...")
    pipeline = transformers.pipeline(
        "text-generation",
        model=MODEL_ID,
        device_map="auto",
    )
    logger.info("Local LLM pipeline initialized successfully on GPU.")
except Exception as e:
    logger.error(f"Failed to initialize local LLM pipeline: {e}", exc_info=True)
    pipeline = None


async def get_llm_response(prompt: str) -> str | None:
    if not pipeline:
        logger.error("Cannot get LLM response because the pipeline is not initialized.")
        return None
    try:
        def _run_inference():
            messages = [{"role": "user", "content": prompt}]
            outputs = pipeline(messages, max_new_tokens=512, do_sample=False)
            generated_text = outputs[0]["generated_text"][-1]["content"]

            json_start_index = generated_text.find("{")
            json_end_index = generated_text.rfind("}")

            if json_start_index != -1 and json_end_index != -1:
                return generated_text[json_start_index : json_end_index + 1]
            logger.warning(f"Could not find JSON in LLM response: {generated_text}")
            return generated_text

        return await asyncio.to_thread(_run_inference)
    except Exception as e:
        logger.error(f"An error occurred while running the local LLM pipeline: {e}", exc_info=True)
        return None