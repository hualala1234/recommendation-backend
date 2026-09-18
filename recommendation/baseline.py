BASELINE_KEYS = (
    "stress",
    "sleep",
    "bodyFatigue",
    "lowEnergy",
    "cognitiveLoad",
)


def normalize_baseline(raw_scores: dict) -> dict:
    """
    將原始 0~3 分轉為 0~1。

    Bi = Qi / 3
    """

    profile = {}

    for key in BASELINE_KEYS:

        if key not in raw_scores:
            raise ValueError(f"缺少 Baseline 欄位：{key}")

        score = float(raw_scores[key])

        if score < 0 or score > 3:
            raise ValueError(
                f"{key} 必須介於 0~3"
            )

        profile[key] = score / 3.0

    return profile


def calculate_baseline_fit(
    baseline_profile: dict,
    candidate_weights: dict
) -> float:
    """
    BaselineFit(s)
    =
    Σ [Bi × Ki(s)] / Σ Bi
    """

    total_load = sum(
        baseline_profile[key]
        for key in BASELINE_KEYS
    )

    # 五個 Baseline 都是 0
    # 計畫書設定為中性值
    if total_load == 0:
        return 0.5

    weighted_sum = 0.0

    for key in BASELINE_KEYS:

        baseline_value = baseline_profile[key]
        fit_value = candidate_weights[key]

        weighted_sum += (
            baseline_value * fit_value
        )

    return weighted_sum / total_load


def rank_candidates(
    baseline_profile: dict,
    matrix: dict
) -> list:
    """
    對矩陣裡所有候選內容計算 BaselineFit，
    並由高到低排序。
    """

    results = []

    for candidate_id, candidate_weights in matrix.items():

        fit = calculate_baseline_fit(
            baseline_profile,
            candidate_weights
        )

        results.append({
            "id": candidate_id,
            "baselineFit": round(fit, 4)
        })

    results.sort(
        key=lambda item: item["baselineFit"],
        reverse=True
    )

    return results