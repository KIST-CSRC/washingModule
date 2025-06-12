import torch
if torch.cuda.is_available():
    print("CUDA is available. PyTorch can use GPU!",torch.__version__)
    print("CUDA Version:", torch.version.cuda)
    torch.cuda.empty_cache()
else:
    print("CUDA is not available. PyTorch is using CPU.")