"""
Generates a synthetic student election dataset for demo/training purposes.
"""
import pandas as pd
import numpy as np
import random

DEPARTMENTS = ["Engineering", "Sciences", "Arts", "Commerce", "Law", "Medicine", "Business"]
CANDIDATE_PREFIXES = ["Juan", "Maria", "Alex", "Jordan", "Taylor", "Morgan", "Casey",
                      "Riley", "Cameron", "Avery", "Rohan", "Priya", "Liam", "Emma",
                      "Noah", "Olivia", "Ethan", "Sophia", "Mason", "Isabella"]
CANDIDATE_SUFFIXES = ["Santos", "Reyes", "Cruz", "Garcia", "Lopez", "Sharma", "Patel",
                      "Singh", "Kumar", "Johnson", "Williams", "Brown", "Davis", "Miller"]


def generate_sample_dataset(n_rows: int = 200, seed: int = 42) -> pd.DataFrame:
    np.random.seed(seed)
    random.seed(seed)

    records = []
    for _ in range(n_rows):
        popularity   = round(np.random.uniform(20, 100), 2)
        spending     = round(np.random.uniform(500, 50000), 2)
        social_media = round(np.random.uniform(10, 100), 2)
        past_perf    = round(np.random.uniform(0, 100), 2)
        engagement   = round(np.random.uniform(10, 100), 2)
        department   = random.choice(DEPARTMENTS)

        # Realistic win probability driven by features
        score = (
            0.30 * popularity +
            0.20 * social_media +
            0.20 * past_perf +
            0.15 * engagement +
            0.10 * (spending / 500) +
            np.random.normal(0, 5)
        )
        winner = 1 if score > 55 else 0

        name = f"{random.choice(CANDIDATE_PREFIXES)} {random.choice(CANDIDATE_SUFFIXES)}"
        records.append({
            "candidate_name": name,
            "popularity_score": popularity,
            "campaign_spending": spending,
            "social_media_score": social_media,
            "department": department,
            "past_performance": past_perf,
            "engagement_level": engagement,
            "election_result": winner,
        })

    df = pd.DataFrame(records)
    return df


if __name__ == "__main__":
    df = generate_sample_dataset()
    print(df.head())
    print(f"\nClass distribution:\n{df['election_result'].value_counts()}")
