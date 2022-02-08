"""Speed comparison test (vs dict)

Usage:
python tools/speed.py
"""
import sys
import random
import copy
import argparse
from pathlib import Path
from datetime import datetime

import pandas as pd

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    SAVEFIG = True
except Exception:
    SAVEFIG = False

pkg_dir = Path(__file__).parents[1]
sys.path.append(str(pkg_dir))
from src.rsdict import __version__, rsdict, rsdict_fixtype
print(rsdict.__module__, __version__)


def measure(d, f, size, n) -> tuple:
    """Returns: (average_time, list(time))"""
    ts = []
    if f.endswith("key"):
        for i in range(n):
            ds = datetime.now()
            for k in range(size):
                if f == "addkey":
                    d[f"new_{i}_{k}"] = 0.5
                elif f == "delkey":
                    del d[f"new_{i}_{k}"]
            de = datetime.now()
            ts.append((de - ds).total_seconds())
    else:
        for _ in range(n):
            ds = datetime.now()
            if f == "get":
                for k in d:
                    x = d[k]
            elif f == "set":
                for k in d:
                    d[k] = 0.5
            else:
                raise ValueError(f)
            de = datetime.now()
            ts.append((de - ds).total_seconds())
    return (sum(ts)/n, ts)


def main(argv) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", "-s", type=int, default=100)
    parser.add_argument("--test", "-t", type=int, default=1000)
    parser.add_argument("--notsave", "-ns", action="count", default=0)

    args = parser.parse_args()
    size = args.size
    n_test = args.test
    savefig = SAVEFIG and not bool(args.notsave)

    nums = [random.random() for _ in range(size)]
    d_init = dict()
    for i in range(size):
        d_init[str(i)] = nums[i]

    results = list()
    funcs = ["get", "set", "addkey", "delkey"]
    for f in funcs:
        if f in ["delkey"]:
            pass
        else:
            # reset
            data = dict()
            data["dict"] = copy.deepcopy(d_init)
            data["rsdict"] = rsdict_fixtype(data["dict"])
            # data["rdd"] = rsdict_fixtype(data["rd"].to_dict())

        t_d = None
        for dname, d in data.items():
            # print(f, dname)
            t = measure(d, f, size, n_test)[0]
            if f in ["addkey"]:
                data[dname] = d
            if dname == "dict":
                t_d = copy.copy(t)
            results.append(dict(
                func=f,
                data=dname,
                time=t / size,
                ratio=t / t_d
            ))

    df = pd.DataFrame.from_dict(results)
    print(df[df["data"] == "rsdict"].set_index("func")["ratio"].to_dict())

    if savefig:
        # figure
        fig = plt.figure(figsize=(5, 2))
        fig.patch.set_facecolor("white")

        # axis
        ax = plt.subplot(111)
        sns.barplot(
            data=df, y="func", x="time",
            hue="data", hue_order=["dict", "rsdict"],
            ax=ax, orient="h")
        ax.set_xticks([])
        ax.set_ylabel("")

        # text
        i = 0
        for i, rect in zip(range(len(funcs)), ax.patches):
            f = funcs[i]
            ax.text(
                rect.get_width() * 2,
                rect.get_y() + rect.get_height() * 1.6,
                "x " + df[
                    (df["func"] == f) * (df["data"] == "rsdict")
                ]["ratio"].round(1).astype(str).values[0],
                horizontalalignment="left",
            )

        # save
        edate = datetime.now().strftime("%Y%m%d%H%M%S")
        filepath = pkg_dir / f"docs/img/speed_{edate}.png"
        print("savefig: " + str(filepath))
        plt.title(f"rsdict v{__version__}, {size}keys, {n_test}times")
        fig.savefig(filepath)
        plt.clf()
        plt.close()


if __name__ == "__main__":
    main(sys.argv)
