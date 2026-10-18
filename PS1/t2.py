import os
import sys
from typing import Any, Dict, List, Optional
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import requests

DEFAULT_API_URL = "https://raw.githubusercontent.com/datasets/student-scores/main/scores.json"
CHART_OUTPUT_FILENAME = "student_scores_barchart.png"
REQUEST_TIMEOUT_SECONDS = 10

MOCK_STUDENT_SCORES = [
    {"student_id": "STU101", "name": "Lakshin Khurana", "score": 88.5},
    {"student_id": "STU102", "name": "Diya Patel", "score": 92.0},
    {"student_id": "STU103", "name": "Rohan Mehta", "score": 74.0},
    {"student_id": "STU104", "name": "Ananya Iyer", "score": 95.5},
    {"student_id": "STU105", "name": "Vikram Singh", "score": 68.0},
    {"student_id": "STU106", "name": "Sneha Nair", "score": 84.0},
    {"student_id": "STU107", "name": "Karan Verma", "score": 79.5},
    {"student_id": "STU108", "name": "Pooja Reddy", "score": 91.0},
    {"student_id": "STU109", "name": "Aditya Joshi", "score": 63.5},
    {"student_id": "STU110", "name": "Neha Gupta", "score": 87.0},
]


def fetch_student_scores(api_url: Optional[str] = None) -> List[Dict[str, Any]]:
    target_url = api_url or DEFAULT_API_URL
    print(f"[+] Attempting to fetch student score data from API: {target_url}")
    try:
        response = requests.get(
            target_url,
            headers={"User-Agent": "AccuKnox-Assessment-Client/1.0"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and len(data) > 0 and "score" in data[0]:
            print(f"[+] Successfully fetched {len(data)} student records from API.")
            return data
        else:
            print("[!] API response format differed from expected schema. Using mock dataset.")
            return MOCK_STUDENT_SCORES

    except requests.exceptions.RequestException as exc:
        print(f"[!] API unavailable ({exc.__class__.__name__}). Using documented mock dataset.")
        return MOCK_STUDENT_SCORES


def calc_statistics(records: List[Dict[str, Any]]) -> Dict[str, float]:
    if not records:
        return {"average": 0.0, "min": 0.0, "max": 0.0, "median": 0.0, "count": 0}

    scores = [float(item["score"]) for item in records if "score" in item]
    if not scores:
        return {"average": 0.0, "min": 0.0, "max": 0.0, "median": 0.0, "count": 0}

    sorted_scores = sorted(scores)
    n = len(sorted_scores)
    average_score = sum(sorted_scores) / n

    if n % 2 == 1:
        median_score = sorted_scores[n // 2]
    else:
        median_score = (sorted_scores[(n // 2) - 1] + sorted_scores[n // 2]) / 2.0

    return {
        "average": round(average_score, 2),
        "median": round(median_score, 2),
        "min": round(sorted_scores[0], 2),
        "max": round(sorted_scores[-1], 2),
        "count": n,
    }


def display_summary_table(
    records: List[Dict[str, Any]], stats: Dict[str, float]
) -> None:
    """
    Prints a formatted table of student scores and summary metrics to stdout.
    """
    avg = stats["average"]

    print("\n" + "=" * 65)
    print(f"{'STUDENT TEST SCORES SUMMARY':^65}")
    print("=" * 65)
    print(f"{'ID':<10} | {'Student Name':<25} | {'Score':<8} | {'Status'}")
    print("-" * 65)

    for item in records:
        student_id = item.get("student_id", "N/A")
        name = item.get("name", "Unknown")
        score = float(item.get("score", 0.0))
        status = "Above Avg" if score >= avg else "Below Avg"
        print(f"{student_id:<10} | {name:<25} | {score:<8.1f} | {status}")

    print("=" * 65)
    print(
        f"Metrics -> Total Students: {stats['count']} | Average: {stats['average']} | "
        f"Median: {stats['median']} | Highest: {stats['max']} | Lowest: {stats['min']}"
    )
    print("=" * 65 + "\n")


def plot_student_scores(
    records: List[Dict[str, Any]],
    stats: Dict[str, float],
    output_path: str = CHART_OUTPUT_FILENAME,
) -> str:
    names = [item.get("name", "Unknown") for item in records]
    scores = [float(item.get("score", 0.0)) for item in records]
    avg_score = stats["average"]

    colors = ["#2b8a3e" if s >= avg_score else "#d9480f" for s in scores]

    plt.figure(figsize=(11, 6))
    bars = plt.bar(names, scores, color=colors, width=0.55, edgecolor="#333333", linewidth=0.8)
    plt.axhline(
        y=avg_score,
        color="#c92a2a",
        linestyle="--",
        linewidth=1.8,
        label=f"Class Average ({avg_score:.2f})",
    )

    for bar in bars:
        height = bar.get_height()
        plt.annotate(
            f"{height:.1f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),  # 4 points vertical offset
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )

    plt.title("Students' Test Scores & Class Average Benchmark", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Student Name", fontsize=11, fontweight="bold")
    plt.ylabel("Test Score (out of 100)", fontsize=11, fontweight="bold")
    plt.ylim(0, 110)
    plt.xticks(rotation=30, ha="right", fontsize=10)
    plt.grid(axis="y", linestyle=":", alpha=0.6)
    plt.legend(loc="upper right", frameon=True)
    plt.tight_layout()

    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"[+] Bar chart successfully generated and saved to: '{output_path}'")
    return os.path.abspath(output_path)


def main() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    chart_file = os.path.join(base_dir, CHART_OUTPUT_FILENAME)
    records = fetch_student_scores()#gets records
    stats = calc_statistics(records)
    display_summary_table(records, stats)
    plot_student_scores(records, stats, chart_file)


if __name__ == "__main__":
    main()
