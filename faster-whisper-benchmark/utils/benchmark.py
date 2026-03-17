import torch
import qai_hub as hub

def run_compile(traced_model, device, input_specs_or_shape):
    if isinstance(input_specs_or_shape, dict):
        input_specs = input_specs_or_shape
    else:
        input_specs = dict(image=input_specs_or_shape)

    compile_job = hub.submit_compile_job(
        model=traced_model,
        device=device,
        input_specs=input_specs,
    )

    assert isinstance(compile_job, hub.CompileJob)
    return compile_job


def run_profile(compiled_job, device):
    profile_job = hub.submit_profile_job(
        model=compiled_job.get_target_model(),
        device=device,
        name=compiled_job.name + "_profiling",
    )

    assert isinstance(profile_job, hub.ProfileJob)
    return profile_job


def get_traced_model(input_shape, model, dtype=torch.float32):
    example_input = torch.rand(input_shape, dtype=dtype)
    with torch.no_grad():
        traced_model = torch.jit.trace(model, example_input)
    return traced_model


def get_traced_model_multi(example_inputs, model):
    with torch.no_grad():
        exported = torch.export.export(model, example_inputs)
    tmp_path = "/tmp/decoder_exported.pt2"
    torch.export.save(exported, tmp_path)
    return tmp_path

def profile_model(traced_model: torch.jit.ScriptModule, device: hub.Device, input_specs: dict) -> dict:
    compiled_model = run_compile(traced_model, device, input_specs)
    profiled_model = run_profile(compiled_model, device)
    return profiled_model.download_profile()

def get_exported_model_multi(example_inputs, model):
    """Use torch.export for decoder (avoids aten::diff ONNX issue)."""
    with torch.no_grad():
        exported = torch.export.export(model, example_inputs)
    tmp_path = "/tmp/decoder_exported.pt2"
    torch.export.save(exported, tmp_path)
    return tmp_path
