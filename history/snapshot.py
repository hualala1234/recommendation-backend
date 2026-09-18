from history.calculator import (
    calculate_recent_state,
    calculate_recent_goal,
    calculate_recent_guidance,
    calculate_recent_effect,
    calculate_recent_intent,
    calculate_explore_score,

    calculate_scene_preference,
    calculate_scene_effect,
    calculate_breathing_effect,
    calculate_technique_effect,
    calculate_guidance_effect,

    calculate_preferred_duration,
    calculate_usage_frequency,
    calculate_completion,
    calculate_preferred_time,
)


def build_history_snapshot(
    sessions: list[dict]
) -> dict:

    return {
        "recentState":
            calculate_recent_state(
                sessions
            ),

        "recentGoal":
            calculate_recent_goal(
                sessions
            ),

        "recentGuidance":
            calculate_recent_guidance(
                sessions
            ),

        "recentEffect":
            calculate_recent_effect(
                sessions
            ),

        "recentIntent":
            calculate_recent_intent(
                sessions
            ),

        "exploreScore":
            calculate_explore_score(
                sessions
            ),

        "scenePreference":
            calculate_scene_preference(
                sessions
            ),

        "sceneEffect":
            calculate_scene_effect(
                sessions
            ),

        "breathingEffect":
            calculate_breathing_effect(
                sessions
            ),

        "techniqueEffect":
            calculate_technique_effect(
                sessions
            ),

        "guidanceEffect":
            calculate_guidance_effect(
                sessions
            ),

        "preferredDuration":
            calculate_preferred_duration(
                sessions
            ),

        "usageFrequency":
            calculate_usage_frequency(
                sessions
            ),

        "completion":
            calculate_completion(
                sessions
            ),

        "preferredTime":
            calculate_preferred_time(
                sessions
            ),
    }