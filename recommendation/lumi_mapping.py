# =========================================================
# Lumi Meditation Context
# -> Second Assessment Mapping
# =========================================================


LUMI_STATE_TO_SECOND_ASSESSMENT = {
    "stressed":
        "tense_anxious",

    "anxious":
        "tense_anxious",

    "fatigued":
        "fatigued_low_energy",

    "overthinking":
        "racing_thoughts",

    "calm":
        "calm_relax",
}


LUMI_GOAL_TO_SECOND_ASSESSMENT = {
    "relax":
        "relax",

    "focus":
        "focus",

    "clear_mind":
        "mental_reset",

    "sleep":
        "sleep",

    "self_soothe":
        "self_compassion",
}


LUMI_GUIDANCE_TO_SECOND_ASSESSMENT = {
    "gentle_companion":
        "gentle_companion",

    "structured_guidance":
        "guided_relaxation",

    "environment_sound":
        "ambient_only",

    "sparse_encouragement":
        "quiet_with_encouragement",
}

def map_lumi_to_second_assessment(
    meditation_context: dict
) -> dict:
    """
    將 Lumi meditationContext
    轉換成 Recommendation System
    既有的 Second Assessment 格式。
    """

    if not isinstance(
        meditation_context,
        dict
    ):
        raise ValueError(
            "meditationContext 格式錯誤"
        )


    # =====================================================
    # 1. Lumi 原始資料
    # =====================================================

    raw_state = (
        meditation_context.get(
            "state"
        )
    )

    raw_goal = (
        meditation_context.get(
            "goal"
        )
    )

    raw_guidance = (
        meditation_context.get(
            "guidancePreference"
        )
    )

    raw_duration = (
        meditation_context.get(
            "duration"
        )
    )


    # =====================================================
    # 2. 必填檢查
    # =====================================================

    if raw_state is None:
        raise ValueError(
            "Lumi meditationContext 缺少 state"
        )

    if raw_goal is None:
        raise ValueError(
            "Lumi meditationContext 缺少 goal"
        )

    if raw_guidance is None:
        raise ValueError(
            "Lumi meditationContext "
            "缺少 guidancePreference"
        )

    if raw_duration is None:
        raise ValueError(
            "Lumi meditationContext 缺少 duration"
        )


    # =====================================================
    # 3. State Mapping
    # =====================================================

    if (
        raw_state
        not in
        LUMI_STATE_TO_SECOND_ASSESSMENT
    ):
        raise ValueError(
            f"未知 Lumi state：{raw_state}"
        )

    current_state = (
        LUMI_STATE_TO_SECOND_ASSESSMENT[
            raw_state
        ]
    )


    # =====================================================
    # 4. Goal Mapping
    # =====================================================

    if (
        raw_goal
        not in
        LUMI_GOAL_TO_SECOND_ASSESSMENT
    ):
        raise ValueError(
            f"未知 Lumi goal：{raw_goal}"
        )

    desired_outcome = (
        LUMI_GOAL_TO_SECOND_ASSESSMENT[
            raw_goal
        ]
    )


    # =====================================================
    # 5. Guidance Mapping
    # =====================================================

    if (
        raw_guidance
        not in
        LUMI_GUIDANCE_TO_SECOND_ASSESSMENT
    ):
        raise ValueError(
            "未知 Lumi guidancePreference："
            f"{raw_guidance}"
        )

    companion_preference = (
        LUMI_GUIDANCE_TO_SECOND_ASSESSMENT[
            raw_guidance
        ]
    )


    # =====================================================
    # 6. Duration
    # =====================================================

    if (
        not isinstance(raw_duration, int)
        or raw_duration <= 0
    ):
        raise ValueError(
            f"無效 Lumi duration：{raw_duration}"
        )


    # =====================================================
    # 7. Response
    # =====================================================

    return {
        "plannedDurationMinutes":
            raw_duration,

        "secondAssessment": {
            "currentState":
                current_state,

            "desiredOutcome":
                desired_outcome,

            "companionPreference":
                companion_preference,
        },
    }