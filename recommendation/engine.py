from firebase.firestore_service import (
    get_initial_assessment_scores,
    get_second_assessment,
    get_history_snapshot,
    save_resolved_guidance,
)

from recommendation.baseline import (
    normalize_baseline,
    rank_candidates,
)

from recommendation.current_context import (
    normalize_current_context,
)

from recommendation.scoring import (
    rank_scene_candidates,
    rank_breathing_candidates,
    rank_technique_candidates,
)

from recommendation.matrices import (
    SCENE_BASELINE_MATRIX,
    BREATHING_BASELINE_MATRIX,
    TECHNIQUE_BASELINE_MATRIX,

    SCENE_STATE_MATRIX,
    SCENE_GOAL_MATRIX,

    BREATHING_STATE_MATRIX,
    BREATHING_GOAL_MATRIX,

    TECHNIQUE_STATE_MATRIX,
    TECHNIQUE_GOAL_MATRIX,
)

from recommendation.guidance import (
    get_guidance_voice_parameters,
    get_guidance_history_fallback,
)

def get_baseline_recommendation(
    user_id: str
) -> dict:

    # 1. Firestore 讀取原始分數
    raw_scores = (
        get_initial_assessment_scores(user_id)
    )

    # 2. 正規化 0~3 → 0~1
    baseline_profile = (
        normalize_baseline(raw_scores)
    )

    # 3. Scene
    scene_ranking = rank_candidates(
        baseline_profile,
        SCENE_BASELINE_MATRIX
    )

    # 4. Breathing
    breathing_ranking = rank_candidates(
        baseline_profile,
        BREATHING_BASELINE_MATRIX
    )

    # 5. Technique
    technique_ranking = rank_candidates(
        baseline_profile,
        TECHNIQUE_BASELINE_MATRIX
    )

    # 6. 測試baseline是否都為0
    baseline_is_neutral = all(
        value == 0
        for value in baseline_profile.values()
    )

    return {
        "userId": user_id,

        "rawScores": raw_scores,

        "baselineProfile": {
            key: round(value, 4)
            for key, value in baseline_profile.items()
        },

        "baselineIsNeutral": baseline_is_neutral,

        "sceneRanking": scene_ranking,
        "breathingRanking": breathing_ranking,
        "techniqueRanking": technique_ranking,

        # 目前只是 Baseline 階段最高候選
        # 不是最終完整推薦
        "baselineTopCandidates": (
            None
            if baseline_is_neutral
            else {
                "scene": scene_ranking[0]["id"],
                "breathing": breathing_ranking[0]["id"],
                "technique": technique_ranking[0]["id"],
            }
        )
    }


def get_current_recommendation(
    user_id: str,
    session_id: str
) -> dict:

    # ======================================================
    # 1. Initial Assessment
    # ======================================================

    raw_scores = (
        get_initial_assessment_scores(
            user_id
        )
    )

    baseline_profile = (
        normalize_baseline(
            raw_scores
        )
    )

    # ======================================================
    # 2. Baseline Rankings
    # ======================================================

    scene_baseline = rank_candidates(
        baseline_profile,
        SCENE_BASELINE_MATRIX
    )

    breathing_baseline = rank_candidates(
        baseline_profile,
        BREATHING_BASELINE_MATRIX
    )

    technique_baseline = rank_candidates(
        baseline_profile,
        TECHNIQUE_BASELINE_MATRIX
    )

    # ======================================================
    # 3. Second Assessment
    # ======================================================

    second_assessment = (
        get_second_assessment(
            user_id,
            session_id
        )
    )

    current_context = (
        normalize_current_context(
            second_assessment
        )
    )

    state = current_context["state"]
    goal = current_context["goal"]

    # ======================================================
    # 4. History Snapshot
    # ======================================================

    history_snapshot = (
        get_history_snapshot(
            user_id
        )
    )

    # ======================================================
    # 5. Scene Ranking
    #
    # 目前仍使用 Cold Start
    # ======================================================

    scene_ranking = (
        rank_scene_candidates(
            state=state,
            goal=goal,
            baseline_ranking=
                scene_baseline,
            state_matrix=
                SCENE_STATE_MATRIX,
            goal_matrix=
                SCENE_GOAL_MATRIX,
            history_snapshot=
                history_snapshot,
        )
    )

    # ======================================================
    # 6. Breathing Ranking
    #
    # 目前仍使用 Cold Start
    # ======================================================

    breathing_ranking = (
        rank_breathing_candidates(
            state=state,
            goal=goal,
            baseline_ranking=
                breathing_baseline,
            state_matrix=
                BREATHING_STATE_MATRIX,
            goal_matrix=
                BREATHING_GOAL_MATRIX,
            history_snapshot=
                history_snapshot,
        )
    )

    # ======================================================
    # 7. Technique Ranking
    #
    # 已納入 Technique History
    # ======================================================

    technique_ranking = (
        rank_technique_candidates(
            state=state,
            goal=goal,
            baseline_ranking=technique_baseline,
            state_matrix=TECHNIQUE_STATE_MATRIX,
            goal_matrix=TECHNIQUE_GOAL_MATRIX,
            history_snapshot=history_snapshot,
        )
    )

    # ======================================================
    # 8. Guidance
    #
    # 優先順序：
    #
    # 1. 本次 Pre Q2 明確選擇
    # 2. 此 Session 已經決定過的 fallback
    # 3. Guidance History
    # 4. Default
    # ======================================================

    current_guidance = (
        current_context.get(
            "guidance"
        )
    )

    stored_guidance = (
        second_assessment.get(
            "resolvedGuidance"
        )
    )

    stored_guidance_source = (
        second_assessment.get(
            "guidanceSource"
        )
    )

    stored_history_key = (
        second_assessment.get(
            "resolvedGuidanceHistoryKey"
        )
    )


    # ======================================================
    # 8-1. 使用者本次有明確 Pre Q2
    # ======================================================

    if (
        isinstance(
            current_guidance,
            str
        )
        and current_guidance.strip()
    ):

        guidance = current_guidance

        guidance_source = (
            "current_explicit_choice"
        )

        guidance_history = None


    # ======================================================
    # 8-2. 沒有 Pre Q2
    # 但這個 Session 之前已經決定過 Guidance
    # → 直接沿用
    # ======================================================

    elif (
        isinstance(
            stored_guidance,
            str
        )
        and stored_guidance.strip()
    ):

        guidance = stored_guidance

        guidance_source = (
            stored_guidance_source
            or "stored_fallback"
        )

        guidance_history = {
            "historyKey":
                stored_history_key,

            "restoredFromSession":
                True,
        }


    # ======================================================
    # 8-3. 沒有 Pre Q2，也還沒決定過
    # → 使用 History
    # ======================================================

    else:

        guidance_history = (
            get_guidance_history_fallback(
                history_snapshot
            )
        )


        if guidance_history is not None:

            guidance = (
                guidance_history[
                    "id"
                ]
            )

            guidance_source = (
                "history_fallback"
            )


            # ==============================================
            # 將這次決定結果存回 secondAssessment
            # ==============================================

            save_resolved_guidance(
                user_id=user_id,
                session_id=session_id,
                guidance=guidance,
                source=guidance_source,
                history_key=
                    guidance_history.get(
                        "historyKey"
                    ),
            )


        # ==================================================
        # 8-4. History 也沒有
        # → Default
        # ==================================================

        else:

            guidance = (
                "gentle_companion"
            )

            guidance_source = (
                "default_fallback"
            )


            save_resolved_guidance(
                user_id=user_id,
                session_id=session_id,
                guidance=guidance,
                source=guidance_source,
                history_key=None,
            )


    # ======================================================
    # Voice Parameters
    # ======================================================

    voice_parameters = (
        get_guidance_voice_parameters(
            guidance
        )
    )

    # ======================================================
    # 9. Response
    # ======================================================

    return {

        "userId":
            user_id,

        "sessionId":
            session_id,

        "currentContext": {
            "state":
                state,

            "goal":
                goal,

            "guidance":
                guidance,

            "durationMinutes":
                current_context[
                    "durationMinutes"
                ],
        },

        "sceneRanking":
            scene_ranking,

        "breathingRanking":
            breathing_ranking,

        "techniqueRanking":
            technique_ranking,

        "recommendation": {
            "scene":
                scene_ranking[0]["id"],

            "breathing":
                breathing_ranking[0]["id"],

            "technique":
                technique_ranking[0]["id"],

            "guidance": {
                "id":
                    guidance,

                "source":
                    guidance_source,

                "voiceParameters":
                    voice_parameters,

                "history":
                    guidance_history,
            },
        }
    }