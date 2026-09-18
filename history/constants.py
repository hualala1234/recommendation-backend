from zoneinfo import ZoneInfo


# =========================================================
# History 時間設定
# =========================================================

HISTORY_TIMEZONE = ZoneInfo("Asia/Taipei")

RECENT_WINDOW_DAYS = 7

TIME_DECAY_BASE = 0.8


# =========================================================
# Recent State
# secondAssessment.currentState
# =========================================================

STATE_CATEGORIES = [
    "tense_anxious",
    "fatigued_low_energy",
    "racing_thoughts",
    "calm_relax",
]


# =========================================================
# Recent Goal
# secondAssessment.desiredOutcome
# =========================================================

GOAL_CATEGORIES = [
    "relax",
    "focus",
    "mental_reset",
    "sleep",
    "self_compassion",
]


# =========================================================
# Recent Guidance
# secondAssessment.companionPreference
# =========================================================

GUIDANCE_CATEGORIES = [
    "gentle_companion",
    "guided_relaxation",
    "ambient_only",
    "quiet_with_encouragement",
]

# =========================================================
# Recent Intent
# thirdAssessment.reuseIntent.key
# =========================================================

INTENT_CATEGORIES = [
    "reuse_same",
    "explore_other",
    "sleep_signal",
]

# =========================================================
# Scene Preference
# Post Q2
# =========================================================

SCENE_PREFERENCE_SCORE_MAPPING = {
    "very_dislike": 1,
    "dislike": 2,
    "okay": 3,
    "like": 4,
    "very_like": 5,
}

# =========================================================
# Bayesian Smoothing
# =========================================================

BAYESIAN_PRIOR_STRENGTH = 2


# =========================================================
# Scene
# Firestore 原始值 → Recommendation canonical key
# =========================================================

SCENE_MAPPING = {
    "森林": "forest",
    "海邊": "ocean",
    "山上": "mountain",
    "高山": "mountain",
    "山群": "mountain",
    "小麥田": "field",
}

SCENE_CATEGORIES = [
    "forest",
    "ocean",
    "mountain",
    "field",
]


# =========================================================
# Breathing
# =========================================================

BREATHING_MAPPING = {
    "relax_478": "four_seven_eight",
    "box_breathing": "box_breathing",
    "deep_breathing": "slow_4_6",
    "focus_breathing": "equal_5_5",
}

BREATHING_CATEGORIES = [
    "four_seven_eight",
    "box_breathing",
    "slow_4_6",
    "equal_5_5",
]


# =========================================================
# Meditation Technique
# Session.technique 已經直接存 canonical key
# =========================================================

TECHNIQUE_CATEGORIES = [
    "breath_awareness",
    "body_scan",
    "grounding",
    "mindfulness",
    "visualization",
    "self_compassion",
]