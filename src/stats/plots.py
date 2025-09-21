import os
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns


def plot_roundness_by_user(data, filepath: Path):
    # Data: list of tuples with (X, Y) values
    x_values, y_values = zip(*data)
    # Scale Y values to percentages
    y_values_percent = [y * 100 for y in y_values]

    sns.set(style="darkgrid", context="talk")
    plt.figure(figsize=(12, 7))
    sns.lineplot(
        x=x_values,
        y=y_values_percent,
        marker="o",
        color="teal",
        linewidth=2.5,
        linestyle="--",
    )
    sns.scatterplot(x=x_values, y=y_values_percent, color="orange", s=100, zorder=5)

    # Set the plot labels and title
    plt.xlabel("X", fontsize=14, fontweight="bold")
    plt.ylabel("Y (%)", fontsize=14, fontweight="bold")
    plt.title("Amazing roundness history for User", fontsize=18, fontweight="bold")

    # Save the plot as a PNG image
    os.makedirs(filepath.parent, exist_ok=True)
    plt.savefig(filepath.as_posix(), dpi=300, bbox_inches="tight")
