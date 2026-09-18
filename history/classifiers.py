# =========================================================
# Recent Effect
# =========================================================

def classify_recent_effect(
    score: float | None
) -> str | None:

    if score is None:
        return None

    if score >= 4.0:
        return "good"

    if score >= 3.0:
        return "normal"

    return "limited"


# =========================================================
# Explore Score
# =========================================================

def classify_explore_score(
    score: float | None
) -> str | None:

    if score is None:
        return None

    if score >= 0.67:
        return "high"

    if score >= 0.33:
        return "medium"

    return "low"

# =========================================================
# Scene Preference
# =========================================================

def classify_scene_preference(
    score: float | None
) -> str | None:

    if score is None:
        return None

    if score >= 4.21:
        return "very_like"

    if score >= 3.41:
        return "like"

    if score >= 2.61:
        return "okay"

    if score >= 1.81:
        return "dislike"

    return "very_dislike"

# =========================================================
# Bayesian Effect 1~5 分分類
# Breathing / Technique 共用
# =========================================================

def classify_effect_level(
    score: float | None
) -> str | None:

    if score is None:
        return None

    if score >= 4.21:
        return "very_high"

    if score >= 3.41:
        return "high"

    if score >= 2.61:
        return "medium"

    if score >= 1.81:
        return "low"

    return "very_low"

# =========================================================
# Preferred Duration
# =========================================================

def classify_preferred_duration(
    minutes: float | None
) -> str | None:

    if minutes is None:
        return None

    if minutes <= 5:
        return "micro_session"

    if minutes <= 15:
        return "standard_short"

    return "deep_immersion"


# =========================================================
# Usage Frequency
# =========================================================

def classify_usage_frequency(
    count_7d: int
) -> str:

    if count_7d == 0:
        return "dormant"

    if count_7d <= 2:
        return "occasional"

    if count_7d <= 4:
        return "habit_building"

    return "high_engagement"


# =========================================================
# Completion
# =========================================================

def classify_completion(
    completion_rate: float | None
) -> str | None:

    if completion_rate is None:
        return None

    if completion_rate >= 0.67:
        return "stable"

    if completion_rate >= 0.33:
        return "normal"

    return "often_ends_early"