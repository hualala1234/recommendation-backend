# ==========================================================
# Scene Baseline Matrix
# ==========================================================

SCENE_BASELINE_MATRIX = {

    "forest": {
        "stress": 0.65,
        "sleep": 0.85,
        "bodyFatigue": 0.85,
        "lowEnergy": 0.85,
        "cognitiveLoad": 0.65,
    },

    "ocean": {
        "stress": 1.00,
        "sleep": 1.00,
        "bodyFatigue": 0.65,
        "lowEnergy": 0.65,
        "cognitiveLoad": 1.00,
    },

    "mountain": {
        "stress": 0.85,
        "sleep": 0.40,
        "bodyFatigue": 0.40,
        "lowEnergy": 0.40,
        "cognitiveLoad": 0.85,
    },

    "field": {
        "stress": 0.40,
        "sleep": 0.65,
        "bodyFatigue": 1.00,
        "lowEnergy": 1.00,
        "cognitiveLoad": 0.40,
    },
}


# ==========================================================
# Breathing Baseline Matrix
# ==========================================================

BREATHING_BASELINE_MATRIX = {

    "4-7-8 呼吸法": {
        "stress": 0.65,
        "sleep": 1.00,
        "bodyFatigue": 0.85,
        "lowEnergy": 0.85,
        "cognitiveLoad": 0.55,
    },

    "4-4-4-4 方形呼吸": {
        "stress": 1.00,
        "sleep": 0.45,
        "bodyFatigue": 0.55,
        "lowEnergy": 0.55,
        "cognitiveLoad": 1.00,
    },

    "深呼吸練習": {
        "stress": 0.85,
        "sleep": 0.85,
        "bodyFatigue": 1.00,
        "lowEnergy": 1.00,
        "cognitiveLoad": 0.85,
    },

    "equal_5_5": {
        "stress": 0.65,
        "sleep": 0.65,
        "bodyFatigue": 0.75,
        "lowEnergy": 0.75,
        "cognitiveLoad": 0.75,
    },
}


# ==========================================================
# Technique Baseline Matrix
# ==========================================================

TECHNIQUE_BASELINE_MATRIX = {

    "breath_awareness": {
        "stress": 0.85,
        "sleep": 0.75,
        "bodyFatigue": 0.75,
        "lowEnergy": 0.75,
        "cognitiveLoad": 1.00,
    },

    "body_scan": {
        "stress": 0.75,
        "sleep": 1.00,
        "bodyFatigue": 1.00,
        "lowEnergy": 1.00,
        "cognitiveLoad": 0.65,
    },

    "grounding": {
        "stress": 1.00,
        "sleep": 0.55,
        "bodyFatigue": 0.75,
        "lowEnergy": 0.75,
        "cognitiveLoad": 0.85,
    },

    "mindfulness": {
        "stress": 0.75,
        "sleep": 0.65,
        "bodyFatigue": 0.65,
        "lowEnergy": 0.65,
        "cognitiveLoad": 0.85,
    },

    "visualization": {
        "stress": 0.65,
        "sleep": 0.85,
        "bodyFatigue": 0.85,
        "lowEnergy": 0.85,
        "cognitiveLoad": 0.55,
    },

    "self_compassion": {
        "stress": 0.85,
        "sleep": 0.75,
        "bodyFatigue": 0.85,
        "lowEnergy": 0.85,
        "cognitiveLoad": 0.65,
    },
}


# ==========================================================
# Scene State Matrix
#
# state:
# stressed
# fatigued
# overthinking
# calm
# ==========================================================

SCENE_STATE_MATRIX = {

    "stressed": {
        "forest": 0.65,
        "ocean": 1.00,
        "mountain": 0.85,
        "field": 0.40,
    },

    "fatigued": {
        "forest": 0.85,
        "ocean": 0.65,
        "mountain": 0.40,
        "field": 1.00,
    },

    "overthinking": {
        "forest": 0.65,
        "ocean": 1.00,
        "mountain": 0.85,
        "field": 0.40,
    },

    "calm": {
        "forest": 0.65,
        "ocean": 0.40,
        "mountain": 0.85,
        "field": 1.00,
    },
}


# ==========================================================
# Scene Goal Matrix
#
# goal:
# relax
# focus
# mental_reset
# sleep_prepare
# self_soothe
# ==========================================================

SCENE_GOAL_MATRIX = {

    "relax": {
        "forest": 1.00,
        "ocean": 0.85,
        "mountain": 0.65,
        "field": 0.65,
    },

    "focus": {
        "forest": 0.65,
        "ocean": 0.40,
        "mountain": 1.00,
        "field": 0.85,
    },

    "mental_reset": {
        "forest": 0.85,
        "ocean": 1.00,
        "mountain": 0.65,
        "field": 0.65,
    },

    "sleep_prepare": {
        "forest": 0.85,
        "ocean": 1.00,
        "mountain": 0.40,
        "field": 0.65,
    },

    "self_soothe": {
        "forest": 1.00,
        "ocean": 0.85,
        "mountain": 0.65,
        "field": 0.65,
    },
}


# ==========================================================
# Breathing State Matrix
# ==========================================================

BREATHING_STATE_MATRIX = {

    "stressed": {
        "4-7-8 呼吸法": 0.65,
        "4-4-4-4 方形呼吸": 1.00,
        "深呼吸練習": 0.85,
        "equal_5_5": 0.65,
    },

    "fatigued": {
        "4-7-8 呼吸法": 0.85,
        "4-4-4-4 方形呼吸": 0.55,
        "深呼吸練習": 1.00,
        "equal_5_5": 0.75,
    },

    "overthinking": {
        "4-7-8 呼吸法": 0.55,
        "4-4-4-4 方形呼吸": 1.00,
        "深呼吸練習": 0.85,
        "equal_5_5": 0.75,
    },

    "calm": {
        "4-7-8 呼吸法": 0.65,
        "4-4-4-4 方形呼吸": 0.65,
        "深呼吸練習": 0.85,
        "equal_5_5": 1.00,
    },
}


# ==========================================================
# Breathing Goal Matrix
# ==========================================================

BREATHING_GOAL_MATRIX = {

    "relax": {
        "4-7-8 呼吸法": 0.85,
        "4-4-4-4 方形呼吸": 0.65,
        "深呼吸練習": 1.00,
        "equal_5_5": 0.75,
    },

    "focus": {
        "4-7-8 呼吸法": 0.45,
        "4-4-4-4 方形呼吸": 1.00,
        "深呼吸練習": 0.65,
        "equal_5_5": 0.85,
    },

    "mental_reset": {
        "4-7-8 呼吸法": 0.65,
        "4-4-4-4 方形呼吸": 0.85,
        "深呼吸練習": 1.00,
        "equal_5_5": 0.75,
    },

    "sleep_prepare": {
        "4-7-8 呼吸法": 1.00,
        "4-4-4-4 方形呼吸": 0.45,
        "深呼吸練習": 0.85,
        "equal_5_5": 0.65,
    },

    "self_soothe": {
        "4-7-8 呼吸法": 0.75,
        "4-4-4-4 方形呼吸": 0.65,
        "深呼吸練習": 1.00,
        "equal_5_5": 0.85,
    },
}


# ==========================================================
# Technique State Matrix
# ==========================================================

TECHNIQUE_STATE_MATRIX = {

    "stressed": {
        "breath_awareness": 0.85,
        "body_scan": 0.75,
        "grounding": 1.00,
        "mindfulness": 0.75,
        "visualization": 0.65,
        "self_compassion": 0.85,
    },

    "fatigued": {
        "breath_awareness": 0.75,
        "body_scan": 1.00,
        "grounding": 0.75,
        "mindfulness": 0.65,
        "visualization": 0.85,
        "self_compassion": 0.85,
    },

    "overthinking": {
        "breath_awareness": 1.00,
        "body_scan": 0.65,
        "grounding": 0.85,
        "mindfulness": 0.85,
        "visualization": 0.55,
        "self_compassion": 0.65,
    },

    "calm": {
        "breath_awareness": 0.85,
        "body_scan": 0.85,
        "grounding": 0.65,
        "mindfulness": 1.00,
        "visualization": 0.85,
        "self_compassion": 0.85,
    },
}


# ==========================================================
# Technique Goal Matrix
# ==========================================================

TECHNIQUE_GOAL_MATRIX = {

    "relax": {
        "breath_awareness": 0.85,
        "body_scan": 1.00,
        "grounding": 0.85,
        "mindfulness": 0.85,
        "visualization": 0.85,
        "self_compassion": 0.85,
    },

    "focus": {
        "breath_awareness": 1.00,
        "body_scan": 0.55,
        "grounding": 0.85,
        "mindfulness": 0.85,
        "visualization": 0.55,
        "self_compassion": 0.45,
    },

    "mental_reset": {
        "breath_awareness": 0.85,
        "body_scan": 0.75,
        "grounding": 1.00,
        "mindfulness": 0.85,
        "visualization": 0.65,
        "self_compassion": 0.65,
    },

    "sleep_prepare": {
        "breath_awareness": 0.75,
        "body_scan": 1.00,
        "grounding": 0.55,
        "mindfulness": 0.65,
        "visualization": 0.85,
        "self_compassion": 0.75,
    },

    "self_soothe": {
        "breath_awareness": 0.75,
        "body_scan": 0.85,
        "grounding": 0.85,
        "mindfulness": 0.75,
        "visualization": 0.75,
        "self_compassion": 1.00,
    },
}