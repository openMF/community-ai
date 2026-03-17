import torch
import torch.nn as nn
from transformers import WhisperForConditionalGeneration

class WhisperEncoderWrapper(nn.Module):
    def __init__(self, model: WhisperForConditionalGeneration) -> None:
        super().__init__()
        self.encoder = model.model.encoder

    def forward(self, input_features: torch.Tensor) -> torch.Tensor:
        return self.encoder(input_features=input_features).last_hidden_state

class WhisperDecoderStepWrapper(nn.Module):
    def __init__(self, model: WhisperForConditionalGeneration) -> None:
        super().__init__()
        self.decoder = model.model.decoder
        self.proj_out = model.proj_out

    def forward(
        self,
        decoder_input_ids: torch.Tensor, 
        encoder_hidden_states: torch.Tensor,
    ) -> torch.Tensor:
        token_ids = decoder_input_ids.to(torch.int32)  
        out = self.decoder(
            input_ids=token_ids,
            encoder_hidden_states=encoder_hidden_states,
            use_cache=False,
            return_dict=True,
        )
        logits = self.proj_out(out.last_hidden_state)
        return logits[:, -1, :]
