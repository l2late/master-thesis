import numpy as np
import pandas as pd

from alphabuilding import constants as global_config


def plot_energy_prices():
    import matplotlib.pyplot as plt
    import seaborn as sns

    df = pd.DataFrame(global_config.ENERGY_PRICE_SCHEDULE, columns=["Hour", "Price"])

    # Plotting
    sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
    plt.figure(figsize=(10, 5))

    # Use 'post' steps: The price at index i is valid for the interval [i, i+1]
    plt.step(
        df["Hour"],
        df["Price"],
        where="post",
        color="#2980b9",
        linewidth=2.5,
        label="Spot Price",
    )

    # Fill area under the stairs
    plt.fill_between(df["Hour"], df["Price"], step="post", alpha=0.2, color="#2980b9")

    # Formatting
    plt.title("24h Energy Price Schedule", fontsize=14, pad=15)
    plt.xlabel("Hour of Day")
    plt.ylabel("Price (€/kWh)")
    plt.xlim(0, 24)
    plt.xticks(np.arange(0, 25, 2))
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    plt.savefig("energy_prices_stairs.png", dpi=300)
    plt.show()
