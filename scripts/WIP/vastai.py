import os

from vastai_sdk import VastAI

# import api key from environment variable or using dotenv

VASTAI_API_KEY = os.getenv("VASTAI_API_KEY")
vast = VastAI(api_key=VASTAI_API_KEY)
geolocation = ["FR", "NO", "DK", "NL"]
offers = vast.search_offers(num_gpus=1, gpu_name="RTX")
available_keys = offers[0].keys()
requested_keys = [
    "gpu_name",
    "geolocation",
    "inet_down",
    "inet_up",
    "cpu_cores",
    "pcie_bw",
    "gpu_mem_bw",
    "gpu_ram",
    # "time_remaining",
]
for key in requested_keys:
    assert key in available_keys, f"{key} not in available keys: {available_keys}"
for offer in offers:
    print({k: offer[k] for k in requested_keys})
