import firebase_admin
from firebase_admin import firestore
from datetime import (
    datetime,
    timedelta,
    time,
    timezone,
)
from zoneinfo import ZoneInfo
from google.cloud.firestore_v1.base_query import FieldFilter


# 初始化 Firebase Admin
try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app()


db = firestore.client()

# 第一份問卷score數字
def _get_score(data: dict, field_name: str) -> float:
    """
    從 Firestore 欄位中取得 score，並確認範圍為 0~3。
    """

    field = data.get(field_name)

    if not isinstance(field, dict):
        raise ValueError(f"缺少或無效的欄位：{field_name}")

    score = field.get("score")

    if score is None:
        raise ValueError(f"{field_name} 缺少 score")

    score = float(score)

    if score < 0 or score > 3:
        raise ValueError(
            f"{field_name}.score 必須介於 0~3，目前為 {score}"
        )

    return score

# 第一份問卷
def get_initial_assessment_scores(user_id: str) -> dict:
    """
    從：
    initialAssessments/{user_id}

    取得五個 Baseline 原始分數。
    """

    doc_ref = (
        db.collection("initialAssessments")
        .document(user_id)
    )

    doc = doc_ref.get()

    if not doc.exists:
        raise LookupError(
            f"找不到使用者 {user_id} 的 initialAssessment"
        )

    data = doc.to_dict()

    return {
        "stress": _get_score(data, "stress"),
        "sleep": _get_score(data, "sleep"),
        "bodyFatigue": _get_score(data, "physical"),
        "lowEnergy": _get_score(data, "energy"),
        "cognitiveLoad": _get_score(data, "cognition"),
    }

# 第二份問卷
def get_second_assessment(
    user_id: str,
    session_id: str
) -> dict:

    doc_ref = (
        db.collection("users")
        .document(user_id)
        .collection("sessions")
        .document(session_id)
    )

    doc = doc_ref.get()

    if not doc.exists:
        raise LookupError(
            f"找不到 session：{session_id}"
        )

    data = doc.to_dict()

    second = data.get(
        "secondAssessment"
    )

    if not isinstance(
        second,
        dict
    ):
        raise ValueError(
            "此 session 尚未完成 secondAssessment"
        )


    # ======================================================
    # 必填欄位
    # ======================================================

    current_state = second.get(
        "currentState"
    )

    desired_outcome = second.get(
        "desiredOutcome"
    )


    if not current_state:
        raise ValueError(
            "secondAssessment 缺少 currentState"
        )

    if not desired_outcome:
        raise ValueError(
            "secondAssessment 缺少 desiredOutcome"
        )


    # ======================================================
    # Guidance 為可選欄位
    #
    # 有值：
    # → 後續使用本次明確選擇
    #
    # 沒值：
    # → None
    # → 後續由 Guidance History fallback
    # ======================================================

    companion_preference = second.get(
        "companionPreference"
    )


    # ======================================================
    # 回傳
    # ======================================================

    return {
        "currentState":
            current_state,

        "desiredOutcome":
            desired_outcome,

        "companionPreference":
            companion_preference,

        "resolvedGuidance":
            second.get(
                "resolvedGuidance"
            ),

        "guidanceSource":
            second.get(
                "guidanceSource"
            ),

        "resolvedGuidanceHistoryKey":
            second.get(
                "resolvedGuidanceHistoryKey"
            ),

        "plannedDurationMinutes":
            data.get(
                "plannedDurationMinutes"
            ),

        "sessionId":
            session_id,

        "userId":
            user_id,
    }

def save_resolved_guidance(
    user_id: str,
    session_id: str,
    guidance: str,
    source: str,
    history_key: str | None = None,
) -> None:

    doc_ref = (
        db.collection("users")
        .document(user_id)
        .collection("sessions")
        .document(session_id)
    )

    doc_ref.update({
        "secondAssessment.resolvedGuidance":
            guidance,

        "secondAssessment.guidanceSource":
            source,

        "secondAssessment.resolvedGuidanceHistoryKey":
            history_key,

        "secondAssessment.guidanceResolvedAt":
            firestore.SERVER_TIMESTAMP,
    })


def get_recent_sessions(
    user_id: str,
    days: int = 28
) -> list[dict]:

    taipei = ZoneInfo(
        "Asia/Taipei"
    )

    today = (
        datetime.now(
            taipei
        ).date()
    )

    # =========================================
    # 最近 N 個日曆日
    #
    # days = 28：
    # 今天 + 前 27 天
    # =========================================

    local_cutoff = (
        datetime.combine(
            today
            - timedelta(
                days=days - 1
            ),
            time.min,
            tzinfo=taipei,
        )
    )

    # Firestore Timestamp 用 UTC 查詢
    cutoff = (
        local_cutoff.astimezone(
            timezone.utc
        )
    )
    sessions_ref = (
        db.collection("users")
        .document(user_id)
        .collection("sessions")
    )

    query = (
        sessions_ref
        .where(
            filter=FieldFilter(
                "startTime",
                ">=",
                cutoff
            )
        )
        .order_by(
            "startTime"
        )
    )

    docs = query.stream()

    sessions = []

    for doc in docs:
        data = doc.to_dict()

        # 把 Firestore document id 一起帶回來
        data["_documentId"] = doc.id

        sessions.append(data)

    return sessions

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


HISTORY_TIMEZONE = ZoneInfo("Asia/Taipei")


def split_history_windows(
    sessions: list[dict]
) -> dict:

    today = datetime.now(
        HISTORY_TIMEZONE
    ).date()

    sessions_7d = []
    sessions_28d = []

    for session in sessions:

        start_time = session.get("startTime")

        if start_time is None:
            continue

        local_start_time = (
            start_time.astimezone(
                HISTORY_TIMEZONE
            )
        )

        days_ago = (
            today
            - local_start_time.date()
        ).days


        # 今天 ～ 6 天前
        if 0 <= days_ago <= 6:
            sessions_7d.append(session)


        # 今天 ～ 27 天前
        if 0 <= days_ago <= 27:
            sessions_28d.append(session)


    return {
        "sessions7d": sessions_7d,
        "sessions28d": sessions_28d
    }

# =========================================================
# Recommendation History Snapshot
# =========================================================

def save_history_snapshot(
    user_id: str,
    history_snapshot: dict,
) -> None:
    """
    將 History 計算結果寫入：

    users/{uid}/recommendationProfile/history
    """

    doc_ref = (
        db.collection("users")
        .document(user_id)
        .collection("recommendationProfile")
        .document("history")
    )


    payload = {
        **history_snapshot,

        # Firestore Server Timestamp
        "updatedAt":
            firestore.SERVER_TIMESTAMP,

        # 之後如果結構有改版，
        # 可以利用 schemaVersion 區分
        "schemaVersion": 1,
    }


    # 整份 Snapshot 覆寫
    #
    # 不使用 merge=True，
    # 避免未來刪除某欄位後，
    # Firestore 還殘留舊欄位。
    doc_ref.set(
        payload
    )

def get_history_snapshot(
    user_id: str
) -> dict | None:
    """
    讀取已儲存的 History Snapshot：

    users/{uid}/recommendationProfile/history
    """

    doc_ref = (
        db.collection("users")
        .document(user_id)
        .collection("recommendationProfile")
        .document("history")
    )


    doc = doc_ref.get()


    if not doc.exists:
        return None


    return doc.to_dict()

def get_all_user_ids() -> list[str]:
    """
    取得 users collection 中所有使用者 UID。
    """

    users_ref = (
        db
        .collection("users")
    )

    docs = users_ref.stream()

    user_ids = [
        doc.id
        for doc in docs
    ]

    return user_ids

def get_lumi_conversation(
    user_id: str,
    conversation_id: str
) -> dict | None:
    """
    讀取指定使用者的 Lumi Conversation。

    Firestore 路徑：
    users/{userId}/lumiConversations/{conversationId}
    """

    doc_ref = (
        db.collection("users")
        .document(user_id)
        .collection("lumiConversations")
        .document(conversation_id)
    )

    doc = doc_ref.get()

    if not doc.exists:
        return None

    return doc.to_dict()

def create_session_from_lumi(
    user_id: str,
    conversation_id: str,
    mapped_data: dict
) -> dict:
    """
    根據 Lumi Mapping 結果建立 Meditation Session。

    Firestore：
    users/{uid}/sessions/{sessionId}
    """

    # =====================================================
    # 1. 基本資料檢查
    # =====================================================

    if not user_id:
        raise ValueError(
            "缺少 user_id"
        )

    if not conversation_id:
        raise ValueError(
            "缺少 conversation_id"
        )

    if not isinstance(
        mapped_data,
        dict
    ):
        raise ValueError(
            "mapped_data 格式錯誤"
        )


    # =====================================================
    # 2. 取得 Mapping 後的資料
    # =====================================================

    planned_duration = (
        mapped_data.get(
            "plannedDurationMinutes"
        )
    )

    second_assessment = (
        mapped_data.get(
            "secondAssessment"
        )
    )


    if (
        not isinstance(
            planned_duration,
            int
        )
        or isinstance(
            planned_duration,
            bool
        )
        or planned_duration <= 0
    ):
        raise ValueError(
            "plannedDurationMinutes 無效"
        )


    if not isinstance(
        second_assessment,
        dict
    ):
        raise ValueError(
            "缺少 secondAssessment"
        )


    # =====================================================
    # 3. Second Assessment 必填欄位
    # =====================================================

    current_state = (
        second_assessment.get(
            "currentState"
        )
    )

    desired_outcome = (
        second_assessment.get(
            "desiredOutcome"
        )
    )

    companion_preference = (
        second_assessment.get(
            "companionPreference"
        )
    )


    if not current_state:
        raise ValueError(
            "secondAssessment 缺少 currentState"
        )

    if not desired_outcome:
        raise ValueError(
            "secondAssessment 缺少 desiredOutcome"
        )

    if not companion_preference:
        raise ValueError(
            "secondAssessment 缺少 companionPreference"
        )


    # =====================================================
    # 4. 建立新的 Session Document
    # =====================================================

    session_ref = (
        db.collection("users")
        .document(user_id)
        .collection("sessions")
        .document()
    )

    session_id = session_ref.id


    # =====================================================
    # 5. Session Data
    # =====================================================

    session_data = {
        "sourceConversationId":
            conversation_id,

        "plannedDurationMinutes":
            planned_duration,

        "isCompleted":
            False,

        "endedEarly":
            False,

        "secondAssessment": {
            "currentState":
                current_state,

            "desiredOutcome":
                desired_outcome,

            "companionPreference":
                companion_preference,

            "submittedAt":
                firestore.SERVER_TIMESTAMP,
        },

        "createdAt":
            firestore.SERVER_TIMESTAMP,
    }


    # =====================================================
    # 6. 寫入 Firestore
    # =====================================================

    session_ref.set(
        session_data
    )


    # =====================================================
    # 7. Response
    # =====================================================

    return {
        "sessionId":
            session_id,

        "userId":
            user_id,

        "sourceConversationId":
            conversation_id,

        "plannedDurationMinutes":
            planned_duration,

        "secondAssessment": {
            "currentState":
                current_state,

            "desiredOutcome":
                desired_outcome,

            "companionPreference":
                companion_preference,
        },
    }


# =========================================================
# Scene Mapping
#
# Firestore Scene Name -> Recommendation ID
# =========================================================

SCENE_MAPPING = {
    "森林": "forest",
    "海邊": "ocean",
    "山上": "mountain",
    "小麥田": "field",
}


# Recommendation ID -> Firestore Scene Name
SCENE_ID_TO_NAME = {
    value: key
    for key, value in SCENE_MAPPING.items()
}


def save_session_recommendation(
    user_id: str,
    session_id: str,
    recommendation_result: dict
) -> dict:
    """
    將 get_current_recommendation() 的結果
    寫回既有 Meditation Session。

    不另外建立 recommendation map。

    寫入：
    - sceneName
    - breathingMode
    - technique

    並更新 secondAssessment：
    - resolvedGuidance
    - guidanceSource
    - resolvedGuidanceHistoryKey
    """

    # =====================================================
    # 1. 基本檢查
    # =====================================================

    if not user_id:
        raise ValueError(
            "缺少 user_id"
        )

    if not session_id:
        raise ValueError(
            "缺少 session_id"
        )

    if not isinstance(
        recommendation_result,
        dict
    ):
        raise ValueError(
            "recommendation_result 格式錯誤"
        )


    # =====================================================
    # 2. 取得 Session
    # =====================================================

    session_ref = (
        db.collection("users")
        .document(user_id)
        .collection("sessions")
        .document(session_id)
    )

    doc = session_ref.get()

    if not doc.exists:
        raise LookupError(
            f"找不到 session：{session_id}"
        )

    session_data = doc.to_dict()


    # =====================================================
    # 3. Recommendation
    # =====================================================

    recommendation = (
        recommendation_result.get(
            "recommendation"
        )
    )

    if not isinstance(
        recommendation,
        dict
    ):
        raise ValueError(
            "推薦結果缺少 recommendation"
        )


    # =====================================================
    # 4. Scene
    # =====================================================

    scene_id = (
        recommendation.get(
            "scene"
        )
    )

    if not scene_id:
        raise ValueError(
            "推薦結果缺少 scene"
        )

    if scene_id not in SCENE_ID_TO_NAME:
        raise ValueError(
            f"未知 scene：{scene_id}"
        )

    scene_name = (
        SCENE_ID_TO_NAME[
            scene_id
        ]
    )


    # =====================================================
    # 5. Breathing
    # =====================================================

    breathing_mode = (
        recommendation.get(
            "breathing"
        )
    )

    if not breathing_mode:
        raise ValueError(
            "推薦結果缺少 breathing"
        )


    # =====================================================
    # 6. Technique
    # =====================================================

    technique = (
        recommendation.get(
            "technique"
        )
    )

    if not technique:
        raise ValueError(
            "推薦結果缺少 technique"
        )


    # =====================================================
    # 7. Guidance
    # =====================================================

    guidance = (
        recommendation.get(
            "guidance"
        )
    )

    if not isinstance(
        guidance,
        dict
    ):
        raise ValueError(
            "推薦結果缺少 guidance"
        )

    resolved_guidance = (
        guidance.get(
            "id"
        )
    )

    guidance_source = (
        guidance.get(
            "source"
        )
    )

    guidance_history = (
        guidance.get(
            "history"
        )
    )

    if not resolved_guidance:
        raise ValueError(
            "guidance 缺少 id"
        )

    if not guidance_source:
        raise ValueError(
            "guidance 缺少 source"
        )


    # =====================================================
    # 8. resolvedGuidanceHistoryKey
    # =====================================================

    resolved_history_key = None


    # -----------------------------------------------------
    # History fallback / Stored fallback
    # -----------------------------------------------------

    if isinstance(
        guidance_history,
        dict
    ):

        resolved_history_key = (
            guidance_history.get(
                "historyKey"
            )
        )


    # -----------------------------------------------------
    # 本次 Lumi 有明確選擇 Guidance
    #
    # 例如：
    #
    # companionPreference
    # = guided_relaxation
    #
    # resolvedGuidance
    # = structured_guidance
    # -----------------------------------------------------

    if (
        not resolved_history_key
        and guidance_source
        == "current_explicit_choice"
    ):

        second_assessment = (
            session_data.get(
                "secondAssessment",
                {}
            )
        )

        if isinstance(
            second_assessment,
            dict
        ):

            resolved_history_key = (
                second_assessment.get(
                    "companionPreference"
                )
            )


    # =====================================================
    # 9. 寫入 Session
    # =====================================================

    update_data = {

        # -------------------------------------------------
        # Meditation Recommendation
        # -------------------------------------------------

        "sceneName":
            scene_name,

        "breathingMode":
            breathing_mode,

        "technique":
            technique,


        # -------------------------------------------------
        # Guidance Resolution
        # -------------------------------------------------

        "secondAssessment.resolvedGuidance":
            resolved_guidance,

        "secondAssessment.guidanceSource":
            guidance_source,

        "secondAssessment.resolvedGuidanceHistoryKey":
            resolved_history_key,


        # -------------------------------------------------
        # Recommendation 完成時間
        # -------------------------------------------------

        "recommendationUpdatedAt":
            firestore.SERVER_TIMESTAMP,
    }


    session_ref.update(
        update_data
    )


    # =====================================================
    # 10. Response
    # =====================================================

    return {
        "userId":
            user_id,

        "sessionId":
            session_id,

        "sceneName":
            scene_name,

        "breathingMode":
            breathing_mode,

        "technique":
            technique,

        "guidanceResolution": {
            "resolvedGuidance":
                resolved_guidance,

            "guidanceSource":
                guidance_source,

            "resolvedGuidanceHistoryKey":
                resolved_history_key,
        },
    }

def update_lumi_session_id(
    user_id: str,
    conversation_id: str,
    session_id: str
) -> dict:
    """
    將 Meditation Session ID
    回填至 Lumi Conversation。

    Firestore：
    users/{uid}/lumiConversations/{conversationId}
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

    if not session_id:
        raise ValueError(
            "缺少 session_id"
        )


    # =====================================================
    # 2. 取得 Lumi Conversation
    # =====================================================

    conversation_ref = (
        db.collection("users")
        .document(user_id)
        .collection("lumiConversations")
        .document(conversation_id)
    )

    doc = conversation_ref.get()

    if not doc.exists:
        raise LookupError(
            f"找不到 Lumi Conversation："
            f"{conversation_id}"
        )

    conversation = doc.to_dict()


    # =====================================================
    # 3. 防止覆蓋其他 Session
    # =====================================================

    existing_session_id = (
        conversation.get(
            "sessionId"
        )
    )

    if (
        existing_session_id
        and existing_session_id != session_id
    ):
        raise ValueError(
            "此 Lumi Conversation "
            "已綁定其他 Session："
            f"{existing_session_id}"
        )


    # =====================================================
    # 4. 回填 Session ID
    # =====================================================

    conversation_ref.update({
        "sessionId":
            session_id,

        "sessionLinkedAt":
            firestore.SERVER_TIMESTAMP,
    })


    # =====================================================
    # 5. Response
    # =====================================================

    return {
        "userId":
            user_id,

        "conversationId":
            conversation_id,

        "sessionId":
            session_id,

        "status":
            "linked",
    }

def get_session(
    user_id: str,
    session_id: str
) -> dict:
    """
    讀取指定 Meditation Session。

    Firestore：
    users/{uid}/sessions/{sessionId}
    """

    session_ref = (
        db.collection("users")
        .document(user_id)
        .collection("sessions")
        .document(session_id)
    )

    doc = session_ref.get()

    if not doc.exists:
        raise LookupError(
            f"找不到 session：{session_id}"
        )

    data = doc.to_dict()

    data["sessionId"] = session_id

    return data