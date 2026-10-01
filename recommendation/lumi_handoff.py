from firebase.firestore_service import (
    get_lumi_conversation,
    get_session,
    create_session_from_lumi,
    save_session_recommendation,
    update_lumi_session_id,
)

from recommendation.lumi_mapping import (
    map_lumi_to_second_assessment,
)

from recommendation.engine import (
    get_current_recommendation,
)


# =========================================================
# Lumi -> Meditation Recommendation
# =========================================================

def prepare_recommendation_from_lumi(
    user_id: str,
    conversation_id: str
) -> dict:
    """
    Lumi Conversation 完成後：

    1. 讀取 Lumi Conversation
    2. 驗證 status / type
    3. Lumi Context -> Second Assessment
    4. 建立 Meditation Session
    5. 執行 Current Recommendation
    6. 推薦結果寫入 Session
    7. Session ID 回填 Lumi Conversation
    8. 回傳 Unity 所需資料

    具有基本 idempotent 行為：
    如果 Conversation 已經有 sessionId，
    不會再次建立 Session。
    """

    # =====================================================
    # 1. 基本檢查
    # =====================================================

    if not user_id:
        raise ValueError(
            "缺少 user_id"
        )

    if not conversation_id:
        raise ValueError(
            "缺少 conversation_id"
        )


    # =====================================================
    # 2. 讀取 Lumi Conversation
    # =====================================================

    conversation = (
        get_lumi_conversation(
            user_id,
            conversation_id
        )
    )

    if conversation is None:
        raise LookupError(
            f"找不到 Lumi Conversation："
            f"{conversation_id}"
        )


    # =====================================================
    # 3. 驗證 Lumi Status
    # =====================================================

    status = conversation.get(
        "status"
    )

    if status != "ready":
        raise ValueError(
            "Lumi Conversation "
            f"尚未 ready，目前 status={status}"
        )


    # =====================================================
    # 4. 確認這次是 Meditation
    # =====================================================

    recommendation_input = (
        conversation.get(
            "recommendationInput"
        )
    )

    if not isinstance(
        recommendation_input,
        dict
    ):
        raise ValueError(
            "Lumi Conversation "
            "缺少 recommendationInput"
        )

    recommendation_type = (
        recommendation_input.get(
            "type"
        )
    )

    if recommendation_type != "meditation":
        raise ValueError(
            "此 Lumi Conversation "
            "不是 meditation"
        )


    # =====================================================
    # 5. 是否已經建立過 Session
    #
    # 防止 Unity 重複呼叫 API
    # =====================================================

    existing_session_id = (
        conversation.get(
            "sessionId"
        )
    )


    if existing_session_id:

        session = get_session(
            user_id,
            existing_session_id
        )

        # -------------------------------------------------
        # 已經有完整 Recommendation
        # → 直接回傳
        # -------------------------------------------------

        scene_name = session.get(
            "sceneName"
        )

        breathing_mode = session.get(
            "breathingMode"
        )

        technique = session.get(
            "technique"
        )


        if (
            scene_name
            and breathing_mode
            and technique
        ):

            second_assessment = (
                session.get(
                    "secondAssessment",
                    {}
                )
            )

            return {
                "status":
                    "ready",

                "alreadyProcessed":
                    True,

                "userId":
                    user_id,

                "conversationId":
                    conversation_id,

                "sessionId":
                    existing_session_id,

                "plannedDurationMinutes":
                    session.get(
                        "plannedDurationMinutes"
                    ),

                "recommendation": {
                    "sceneName":
                        scene_name,

                    "breathingMode":
                        breathing_mode,

                    "technique":
                        technique,

                    "guidance": {
                        "resolvedGuidance":
                            second_assessment.get(
                                "resolvedGuidance"
                            ),

                        "guidanceSource":
                            second_assessment.get(
                                "guidanceSource"
                            ),

                        "resolvedGuidanceHistoryKey":
                            second_assessment.get(
                                "resolvedGuidanceHistoryKey"
                            ),
                    },
                },
            }


        # -------------------------------------------------
        # Session 已建立
        # 但 Recommendation 還沒完成
        #
        # 代表先前流程可能中途中斷
        # → 從 Recommendation 階段繼續
        # -------------------------------------------------

        recommendation_result = (
            get_current_recommendation(
                user_id,
                existing_session_id
            )
        )

        save_result = (
            save_session_recommendation(
                user_id=user_id,
                session_id=
                    existing_session_id,
                recommendation_result=
                    recommendation_result,
            )
        )

        return {
            "status":
                "ready",

            "alreadyProcessed":
                False,

            "resumed":
                True,

            "userId":
                user_id,

            "conversationId":
                conversation_id,

            "sessionId":
                existing_session_id,

            "plannedDurationMinutes":
                session.get(
                    "plannedDurationMinutes"
                ),

            "recommendation": {
                "sceneName":
                    save_result[
                        "sceneName"
                    ],

                "breathingMode":
                    save_result[
                        "breathingMode"
                    ],

                "technique":
                    save_result[
                        "technique"
                    ],

                "guidance":
                    save_result[
                        "guidanceResolution"
                    ],
            },
        }


    # =====================================================
    # 6. 取得 Meditation Context
    # =====================================================

    meditation_context = (
        conversation.get(
            "meditationContext"
        )
    )

    if not isinstance(
        meditation_context,
        dict
    ):
        raise ValueError(
            "Lumi Conversation "
            "缺少 meditationContext"
        )


    # =====================================================
    # 7. Lumi -> Second Assessment Mapping
    # =====================================================

    mapped_data = (
        map_lumi_to_second_assessment(
            meditation_context
        )
    )


    # =====================================================
    # 8. 建立 Meditation Session
    # =====================================================

    session = (
        create_session_from_lumi(
            user_id=user_id,
            conversation_id=
                conversation_id,
            mapped_data=mapped_data,
        )
    )

    session_id = (
        session[
            "sessionId"
        ]
    )


    # =====================================================
    # 9. 先回填 sessionId
    #
    # 正式流程建議建立 Session 後就先綁定，
    # 避免後續 API Retry 又建立另一個 Session。
    # =====================================================

    update_lumi_session_id(
        user_id=user_id,
        conversation_id=
            conversation_id,
        session_id=session_id,
    )


    # =====================================================
    # 10. 執行真正 Recommendation Engine
    # =====================================================

    recommendation_result = (
        get_current_recommendation(
            user_id,
            session_id
        )
    )


    # =====================================================
    # 11. Recommendation 寫入 Session
    #
    # 寫入：
    # sceneName
    # breathingMode
    # technique
    #
    # secondAssessment：
    # resolvedGuidance
    # guidanceSource
    # resolvedGuidanceHistoryKey
    # =====================================================

    save_result = (
        save_session_recommendation(
            user_id=user_id,
            session_id=session_id,
            recommendation_result=
                recommendation_result,
        )
    )


    # =====================================================
    # 12. 回傳 Unity
    # =====================================================

    return {
        "status":
            "ready",

        "alreadyProcessed":
            False,

        "userId":
            user_id,

        "conversationId":
            conversation_id,

        "sessionId":
            session_id,

        "plannedDurationMinutes":
            mapped_data[
                "plannedDurationMinutes"
            ],

        "currentContext":
            recommendation_result.get(
                "currentContext"
            ),

        "recommendation": {
            "sceneName":
                save_result[
                    "sceneName"
                ],

            "breathingMode":
                save_result[
                    "breathingMode"
                ],

            "technique":
                save_result[
                    "technique"
                ],

            "guidance":
                save_result[
                    "guidanceResolution"
                ],
        },
    }