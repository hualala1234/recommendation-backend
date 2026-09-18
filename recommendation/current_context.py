# 第二份問卷 mapping
from recommendation.mappings import (
    STATE_MAPPING,
    GOAL_MAPPING,
    GUIDANCE_MAPPING,
)


def normalize_current_context(
    second_assessment: dict
) -> dict:

    # ======================================================
    # State
    # ======================================================

    raw_state = (
        second_assessment[
            "currentState"
        ]
    )


    if raw_state not in STATE_MAPPING:
        raise ValueError(
            f"未知 currentState：{raw_state}"
        )


    state = (
        STATE_MAPPING[
            raw_state
        ]
    )


    # ======================================================
    # Goal
    # ======================================================

    raw_goal = (
        second_assessment[
            "desiredOutcome"
        ]
    )


    if raw_goal not in GOAL_MAPPING:
        raise ValueError(
            f"未知 desiredOutcome：{raw_goal}"
        )


    goal = (
        GOAL_MAPPING[
            raw_goal
        ]
    )


    # ======================================================
    # Guidance
    #
    # Guidance 與 State / Goal 不同：
    #
    # 有 Pre Q2
    # → 使用本次明確選擇
    #
    # 沒有 Pre Q2
    # → 回傳 None
    # → 交給 engine.py 做 History fallback
    # ======================================================

    raw_guidance = (
        second_assessment.get(
            "companionPreference"
        )
    )


    if (
        raw_guidance is None
        or (
            isinstance(raw_guidance, str)
            and not raw_guidance.strip()
        )
    ):

        guidance = None


    else:

        if raw_guidance not in GUIDANCE_MAPPING:
            raise ValueError(
                "未知 companionPreference："
                f"{raw_guidance}"
            )

        guidance = (
            GUIDANCE_MAPPING[
                raw_guidance
            ]
        )

    # ======================================================
    # Response
    # ======================================================

    return {
        "state":
            state,

        "goal":
            goal,

        "guidance":
            guidance,

        "durationMinutes":
            second_assessment.get(
                "plannedDurationMinutes"
            ),
    }