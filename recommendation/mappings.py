# 第二份問卷的mapping
STATE_MAPPING = {
    "tense_anxious": "stressed",
    "fatigued_low_energy": "fatigued",
    "racing_thoughts": "overthinking",
    "calm_relax": "calm",
}

GOAL_MAPPING = {
    "relax": "relax",
    "focus": "focus",
    "mental_reset": "mental_reset",
    "sleep": "sleep_prepare",
    "self_compassion": "self_soothe",
}

GUIDANCE_MAPPING = {
    "gentle_companion": "gentle_companion",
    "guided_relaxation": "structured_guidance",
    "ambient_only": "ambient_minimal",
    "quiet_with_encouragement": "sparse_encouragement",
}

# ==========================================================
# Scene Mapping
# Unity / Firestore -> Recommendation Engine
# ==========================================================

SCENE_MAPPING = {
    "森林": "forest",
    "海邊": "ocean",
    "高山": "mountain",
    "小麥田": "field",
}


# ==========================================================
# Breathing Mapping
# Unity / Firestore -> Recommendation Engine
# ==========================================================

BREATHING_MAPPING = {
    # Unity: 4-7-8
    "relax_478": "four_seven_eight",

    # Unity: 4-4-4-4
    "box_breathing": "box_breathing",

    # Unity: 4-2-6-2
    # 推薦系統目前歸類為慢呼吸
    "deep_breathing": "slow_4_6",

    # Unity: 5-5
    "focus_breathing": "equal_5_5",
}