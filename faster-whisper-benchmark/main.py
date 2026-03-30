import torch
import qai_hub as hub
from transformers import WhisperForConditionalGeneration
import wandb
import argparse
import pandas as pd

from models import WhisperEncoderWrapper, WhisperDecoderStepWrapper
from utils import get_traced_model, get_traced_model_multi, profile_model
from metrics.extractor import extract_metrics_from_profile

parser = argparse.ArgumentParser('Faster Whisper Benchmark')

parser.add_argument('--model_id', type=str, default="openai/whisper-small", help='Model ID to benchmark')
parser.add_argument('--batch_size', type=int, default=1, help='Batch size for benchmarking')
parser.add_argument('--decoder_len', type=int, default=16, help='Decoder input length for benchmarking')
parser.add_argument('--tokens', type=int, default=120, help='Estimated number of output tokens to calculate total latency')
parser.add_argument('--feature_length', type=int, default=3000, help='Feature length to benchmark')

parser.add_argument('--wandb_project', type=str, default="faster-whisper-benchmark", help='Weights & Biases project name')
parser.add_argument('--wandb_mode', type=str, choices=['online', 'offline'], default="online", help='Weights & Biases mode (online/offline)')

args, _ = parser.parse_known_args()

# Keep the devices you want to run the benchmark on
devices_list = [
    # "Google Pixel 3a",
    # "Samsung Galaxy S24 (Family)",
    "Samsung Galaxy S25 Ultra"
]

def main():

    for device in devices_list:

        if args.wandb_mode != 'disabled':
            wandb.init(
                project = args.wandb_project,
                name = f"Model: {args.model_id}, Device: {device},",
                mode = args.wandb_mode,
                config = vars(args)
            )

        device = hub.Device(device)
        base_model = WhisperForConditionalGeneration.from_pretrained(args.model_id).eval().cpu()
        encoder_model = WhisperEncoderWrapper(base_model).eval().cpu()
        decoder_model = WhisperDecoderStepWrapper(base_model).eval().cpu()

        encoder_shape = (args.batch_size, 80, args.feature_length)
        print(f"Benchmarking feature shape: {encoder_shape}")

        # Perform benchmarking for encoder
        encoder_profile = profile_model(
            get_traced_model(encoder_shape, encoder_model),
            device,
            {"input_features": encoder_shape},
        )

        encoder_metrics = extract_metrics_from_profile(encoder_profile)

        with torch.no_grad():
            dummy_features = torch.rand(encoder_shape, dtype=torch.float32)
            encoder_hidden = encoder_model(dummy_features)
            encoder_hidden_shape = tuple(encoder_hidden.shape)


        decoder_input = torch.ones((args.batch_size, args.decoder_len), dtype=torch.int32)

        # Perform benchmarking for decoder
        decoder_profile = profile_model(
            get_traced_model_multi((decoder_input, encoder_hidden), decoder_model),
            device,
            {
                "decoder_input_ids": (tuple(decoder_input.shape), "int32"),
                "encoder_hidden_states": (encoder_hidden_shape, "float32"),
            },
        )

        decoder_metrics = extract_metrics_from_profile(decoder_profile)

        enc_ms = encoder_metrics.get("estimated_inference_time_ms")
        dec_ms = decoder_metrics.get("estimated_inference_time_ms")
        est_total_ms = None
        if enc_ms is not None and dec_ms is not None:
            est_total_ms = enc_ms + args.tokens * dec_ms


        # Combine total memory usage (sum encoder and decoder peak memory)
        encoder_mem = encoder_metrics.get("estimated_inference_peak_memory", 0)
        decoder_mem = decoder_metrics.get("estimated_inference_peak_memory", 0)
        total_memory_mb = encoder_mem + decoder_mem

        all_metrics = {
            "estimated_total_latency_ms": est_total_ms,
            "total_memory_mb": total_memory_mb,
            "encoder": encoder_metrics,
            "decoder": decoder_metrics,
        }

        if args.wandb_mode != 'disabled':
            wandb.log(all_metrics)
            wandb.finish()


if __name__ == "__main__":
    main()
