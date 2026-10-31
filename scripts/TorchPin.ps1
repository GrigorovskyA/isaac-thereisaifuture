# Torch is pinned here, not in requirements-lock.txt, so its wheel index stays explicit.
# Dot-sourced by Bootstrap.ps1 and Check.ps1. The Windows learner uses the CUDA 13.0 build
# (RTX 4070, driver 610.88; CUDA 13.0 needs 580 or newer). -CpuTorch selects the CPU build for a
# machine without an NVIDIA GPU; such a machine cannot train a `device: cuda` lineage.
$TorchCudaVersion = '2.14.1+cu130'
$TorchCudaIndex = 'https://download.pytorch.org/whl/cu130'
$TorchCpuVersion = '2.14.1+cpu'
$TorchCpuIndex = 'https://download.pytorch.org/whl/cpu'
