# =========================================================
# CRM Sync Payload Builder
#
# Firestore History Snapshot
# -> Vital CRM 一般欄位 + 標籤
# =========================================================

from crm.mappings import (
    RECENT_STATE_CRM_VALUES,
    RECENT_GOAL_CRM_VALUES,
    RECENT_GUIDANCE_CRM_VALUES,

    RECENT_EFFECT_TAGS,

    RECENT_INTENT_CRM_VALUES,
    RECENT_INTENT_TAGS,

    SCENE_CRM_VALUES,

    USAGE_FREQUENCY_TAGS,
    COMPLETION_TAGS,

    TECHNIQUE_CRM_VALUES,
    TECHNIQUE_EFFECT_TAGS,
    HIGH_EFFECT_TECHNIQUE_THRESHOLD,

    PREFERRED_TIME_CRM_VALUES,
)

from history.classifiers import (
    classify_effect_level,
)

from datetime import datetime
from zoneinfo import ZoneInfo

CRM_DYNAMIC_FIELDS = [
    "近期主要狀態",
    "近期主要目標",
    "近期引導偏好",
    "近7日平均放鬆分數",
    "近期效果分數",
    "近期使用意願",
    "偏好場景",
    "偏好時長",
    "近期完成率",
    "常用時段",
    "高效果冥想技巧",
]

# =========================================================
# Helper
# =========================================================

def _safe_dict(value) -> dict:
    if isinstance(value, dict):
        return value

    return {}


def _safe_number(value):
    if isinstance(value, (int, float)):
        return value

    return None

# =========================================================
# Last Usage Date
#
# 取最近一筆有 startTime 的 Session，
# 轉成台灣時間 yyyy/MM/dd
# =========================================================

def _get_last_usage_date(
    sessions: list,
) -> str | None:

    if not isinstance(sessions, list):
        return None

    taipei_tz = ZoneInfo(
        "Asia/Taipei"
    )

    valid_times = []


    for session in sessions:

        if not isinstance(
            session,
            dict
        ):
            continue


        start_time = session.get(
            "startTime"
        )


        if start_time is None:
            continue


        # -----------------------------------------
        # Firestore Timestamp
        # 通常讀出來就是 datetime
        # -----------------------------------------

        if isinstance(
            start_time,
            datetime
        ):

            dt = start_time


        # -----------------------------------------
        # 字串格式備援
        # -----------------------------------------

        elif isinstance(
            start_time,
            str
        ):

            try:

                dt = datetime.fromisoformat(
                    start_time.replace(
                        "Z",
                        "+00:00"
                    )
                )

            except ValueError:
                continue


        else:
            continue


        # -----------------------------------------
        # 時區處理
        # -----------------------------------------

        if dt.tzinfo is None:

            dt = dt.replace(
                tzinfo=taipei_tz
            )

        else:

            dt = dt.astimezone(
                taipei_tz
            )


        valid_times.append(
            dt
        )


    if not valid_times:
        return None


    latest_time = max(
        valid_times
    )


    return latest_time.strftime(
        "%Y/%m/%d"
    )

# =========================================================
# Preferred Scene
#
# 從 scenePreference.items 中：
# 只看 hasData = true
# 選 preference 最高者。
# =========================================================

def _get_preferred_scene(
    history: dict,
) -> str | None:

    scene_preference = _safe_dict(
        history.get(
            "scenePreference"
        )
    )

    items = _safe_dict(
        scene_preference.get(
            "items"
        )
    )

    candidates = []


    for scene, item in items.items():

        if not isinstance(item, dict):
            continue

        if not item.get(
            "hasData",
            False,
        ):
            continue

        preference = _safe_number(
            item.get(
                "preference"
            )
        )

        if preference is None:
            continue

        sample_count = (
            item.get(
                "sampleCount",
                0,
            )
        )

        if not isinstance(
            sample_count,
            (int, float),
        ):
            sample_count = 0


        candidates.append(
            (
                scene,
                float(preference),
                int(sample_count),
            )
        )


    if not candidates:
        return None


    # preference 高者優先
    # 同分時 sampleCount 較多者優先
    candidates.sort(
        key=lambda x: (
            x[1],
            x[2],
        ),
        reverse=True,
    )


    scene_key = (
        candidates[0][0]
    )


    return (
        SCENE_CRM_VALUES.get(
            scene_key
        )
    )


# =========================================================
# High Effect Techniques
#
# CRM 欄位：
# 高效果冥想技巧
#
# 條件：
# hasData = true
# effect >= 3.41
#
# CRM 是複選欄位，
# 多個值最後用 "," 串起來。
# =========================================================

def _get_high_effect_techniques(
    history: dict,
) -> list[str]:

    technique_effect = _safe_dict(
        history.get(
            "techniqueEffect"
        )
    )

    items = _safe_dict(
        technique_effect.get(
            "items"
        )
    )

    result = []


    for technique, item in items.items():

        if not isinstance(item, dict):
            continue

        if not item.get(
            "hasData",
            False,
        ):
            continue


        effect = _safe_number(
            item.get(
                "effect"
            )
        )


        if effect is None:
            continue


        if (
            effect
            < HIGH_EFFECT_TECHNIQUE_THRESHOLD
        ):
            continue


        crm_name = (
            TECHNIQUE_CRM_VALUES.get(
                technique
            )
        )


        if crm_name is None:
            continue


        result.append(
            (
                crm_name,
                float(effect),
            )
        )


    # 效果高 → 低
    result.sort(
        key=lambda x: x[1],
        reverse=True,
    )


    return [
        item[0]
        for item in result
    ]


# =========================================================
# Technique Effect Tag
#
# 目前 CRM 的：
#
# 高效果冥想技巧/
#   極高效果冥想技巧
#   高效果冥想技巧
#   中等效果冥想技巧
#   低效果冥想技巧
#   極低效果冥想技巧
#
# 使用「目前有實際資料的 Technique 中，
# effect 最高的那一個」決定使用者標籤。
# =========================================================

def _get_technique_effect_tag(
    history: dict,
) -> str | None:

    technique_effect = _safe_dict(
        history.get(
            "techniqueEffect"
        )
    )

    items = _safe_dict(
        technique_effect.get(
            "items"
        )
    )


    effects = []


    for item in items.values():

        if not isinstance(item, dict):
            continue

        if not item.get(
            "hasData",
            False,
        ):
            continue


        effect = _safe_number(
            item.get(
                "effect"
            )
        )


        if effect is not None:
            effects.append(
                float(effect)
            )


    if not effects:
        return None


    best_effect = max(
        effects
    )


    level = (
        classify_effect_level(
            best_effect
        )
    )


    if level is None:
        return None


    return (
        TECHNIQUE_EFFECT_TAGS.get(
            level
        )
    )


# =========================================================
# Preferred Time
#
# CRM 欄位目前使用單選，
# 所以 preferredTime.primary 若有兩個，
# 先取第一個。
# =========================================================

def _get_preferred_times(
    history: dict,
) -> list[str]:

    preferred_time = _safe_dict(
        history.get("preferredTime")
    )

    primary = preferred_time.get(
        "primary"
    )

    if not isinstance(
        primary,
        list
    ):
        return []


    result = []


    for time_key in primary:

        crm_value = (
            PREFERRED_TIME_CRM_VALUES.get(
                time_key
            )
        )

        if crm_value:
            result.append(
                crm_value
            )


    return result


# =========================================================
# Build CRM Payload
# =========================================================

def build_crm_sync_payload(
    user_id: str,
    history: dict,
    sessions: list | None = None,
) -> dict:

    if not isinstance(
        history,
        dict,
    ):
        raise ValueError(
            "history 必須是 dict"
        )


    extended_fields = {
        field_name: ""
        for field_name
        in CRM_DYNAMIC_FIELDS
    }

    labels = []


    # =====================================================
    # FirebaseUid
    # =====================================================

    extended_fields[
        "FirebaseUid"
    ] = user_id


    # =========================================================
    # Last Usage Date
    # =========================================================

    last_usage_date = (
        _get_last_usage_date(
            sessions
        )
    )

    if last_usage_date:

        extended_fields[
            "最後使用日"
        ] = last_usage_date


    # =====================================================
    # Recent State
    # =====================================================

    recent_state = _safe_dict(
        history.get(
            "recentState"
        )
    )

    state_key = recent_state.get(
        "top"
    )

    if state_key:

        state_value = (
            RECENT_STATE_CRM_VALUES.get(
                state_key
            )
        )

        if state_value:
            extended_fields[
                "近期主要狀態"
            ] = state_value


    # =====================================================
    # Recent Goal
    # =====================================================

    recent_goal = _safe_dict(
        history.get(
            "recentGoal"
        )
    )

    goal_key = recent_goal.get(
        "top"
    )

    if goal_key:

        goal_value = (
            RECENT_GOAL_CRM_VALUES.get(
                goal_key
            )
        )

        if goal_value:
            extended_fields[
                "近期主要目標"
            ] = goal_value


    # =====================================================
    # Recent Guidance
    # =====================================================

    recent_guidance = _safe_dict(
        history.get(
            "recentGuidance"
        )
    )

    guidance_key = (
        recent_guidance.get(
            "top"
        )
    )

    if guidance_key:

        guidance_value = (
            RECENT_GUIDANCE_CRM_VALUES.get(
                guidance_key
            )
        )

        if guidance_value:

            extended_fields[
                "近期引導偏好"
            ] = guidance_value


    # =====================================================
    # Recent Effect
    # =====================================================

    recent_effect = _safe_dict(
        history.get(
            "recentEffect"
        )
    )

    recent_effect_score = (
        _safe_number(
            recent_effect.get(
                "score"
            )
        )
    )


    if recent_effect_score is not None:

        # 你 CRM 現在有這兩個欄位，
        # 目前皆對應最近 7 天 Post Q1 的效果分數。

        extended_fields[
            "近7日平均放鬆分數"
        ] = round(
            recent_effect_score,
            4,
        )

        extended_fields[
            "近期效果分數"
        ] = round(
            recent_effect_score,
            4,
        )


    recent_effect_level = (
        recent_effect.get(
            "level"
        )
    )


    if recent_effect_level:

        tag = (
            RECENT_EFFECT_TAGS.get(
                recent_effect_level
            )
        )

        if tag:
            labels.append(
                tag
            )


    # =====================================================
    # Recent Intent
    # =====================================================

    recent_intent = _safe_dict(
        history.get(
            "recentIntent"
        )
    )

    intent_key = (
        recent_intent.get(
            "top"
        )
    )


    if intent_key:

        intent_value = (
            RECENT_INTENT_CRM_VALUES.get(
                intent_key
            )
        )

        if intent_value:

            extended_fields[
                "近期使用意願"
            ] = intent_value


        intent_tag = (
            RECENT_INTENT_TAGS.get(
                intent_key
            )
        )

        if intent_tag:
            labels.append(
                intent_tag
            )


    # =====================================================
    # Preferred Scene
    # =====================================================

    preferred_scene = (
        _get_preferred_scene(
            history
        )
    )


    if preferred_scene:

        extended_fields[
            "偏好場景"
        ] = preferred_scene


    # =====================================================
    # Preferred Duration
    # =====================================================

    preferred_duration = _safe_dict(
        history.get(
            "preferredDuration"
        )
    )

    duration_minutes = (
        _safe_number(
            preferred_duration.get(
                "minutes"
            )
        )
    )


    if duration_minutes is not None:

        extended_fields[
            "偏好時長"
        ] = round(
            duration_minutes,
            2,
        )


    # =====================================================
    # Usage Frequency
    # =====================================================

    usage_frequency = _safe_dict(
        history.get(
            "usageFrequency"
        )
    )

    count_7d = (
        usage_frequency.get(
            "count7d"
        )
    )


    if isinstance(
        count_7d,
        (int, float),
    ):

        extended_fields[
            "近7日使用次數"
        ] = int(
            count_7d
        )


    usage_level = (
        usage_frequency.get(
            "level"
        )
    )


    if usage_level:

        tag = (
            USAGE_FREQUENCY_TAGS.get(
                usage_level
            )
        )

        if tag:
            labels.append(
                tag
            )


    # =====================================================
    # Completion
    # =====================================================

    completion = _safe_dict(
        history.get(
            "completion"
        )
    )

    completion_rate = (
        _safe_number(
            completion.get(
                "rate"
            )
        )
    )


    if completion_rate is not None:

        extended_fields[
            "近期完成率"
        ] = round(
            completion_rate,
            4,
        )


    completion_level = (
        completion.get(
            "level"
        )
    )


    if completion_level:

        tag = (
            COMPLETION_TAGS.get(
                completion_level
            )
        )

        if tag:
            labels.append(
                tag
            )


    # =====================================================
    # Preferred Time
    # =====================================================

    preferred_times = (
        _get_preferred_times(
            history
        )
    )


    if preferred_times:

        extended_fields[
            "常用時段"
        ] = ",".join(
            preferred_times
        )


    # =====================================================
    # High Effect Techniques
    #
    # Vital CRM 複選欄位：
    # "身體掃描,正念"
    # =====================================================

    high_effect_techniques = (
        _get_high_effect_techniques(
            history
        )
    )


    if high_effect_techniques:

        extended_fields[
            "高效果冥想技巧"
        ] = ",".join(
            high_effect_techniques
        )


    # =====================================================
    # Technique Effect Tag
    # =====================================================

    technique_tag = (
        _get_technique_effect_tag(
            history
        )
    )


    if technique_tag:
        labels.append(
            technique_tag
        )


    # =====================================================
    # 去除重複標籤
    # =====================================================

    labels = list(
        dict.fromkeys(
            labels
        )
    )


    # =====================================================
    # Response
    # =====================================================

    return {
        "extendedFields":
            extended_fields,

        "labels":
            labels,
    }

# =========================================================
# Full CRM Sync
#
# History
# -> CRM Fields
# -> CRM Labels
# =========================================================

from crm.vital_crm_service import (
    search_customer_by_firebase_uid,
    update_customer_extended_fields,
    sync_customer_labels,
)


def sync_user_to_crm(
    user_id: str,
    history: dict,
    sessions: list | None = None,
) -> dict:

    # =====================================================
    # 1. Build CRM Payload
    # =====================================================

    crm_payload = (
        build_crm_sync_payload(
            user_id=user_id,
            history=history,
            sessions=sessions,
        )
    )

    # =====================================================
    # 2. Search CRM Customer
    # =====================================================

    customer_result = (
        search_customer_by_firebase_uid(
            user_id
        )
    )


    if not customer_result.get(
        "success"
    ):

        return {
            "success": False,
            "stage":
                "search_customer",

            "customerResult":
                customer_result,
        }


    if not customer_result.get(
        "found"
    ):

        return {
            "success": False,
            "stage":
                "search_customer",

            "message":
                "找不到 FirebaseUid 對應的 CRM 客戶",
        }


    customers = (
        customer_result.get(
            "customers",
            []
        )
    )


    # FirebaseUid 應該唯一
    if len(customers) != 1:

        return {
            "success": False,
            "stage":
                "search_customer",

            "message":
                "FirebaseUid 對應的 CRM 客戶數量不是 1",

            "count":
                len(customers),
        }


    customer = customers[0]


    customer_id = (
        customer.get(
            "CustomerId"
        )
    )

    customer_no = (
        customer.get(
            "CustomerNo"
        )
    )


    if not customer_id:

        return {
            "success": False,
            "stage":
                "search_customer",

            "message":
                "CRM CustomerId 不存在",
        }


    if not customer_no:

        return {
            "success": False,
            "stage":
                "search_customer",

            "message":
                "CRM CustomerNo 不存在",
        }


    # =====================================================
    # 3. Update CRM Extended Fields
    # =====================================================

    field_result = (
        update_customer_extended_fields(
            customer_id=
                customer_id,

            customer_no=
                customer_no,

            extended_fields=
                crm_payload[
                    "extendedFields"
                ],
        )
    )


    # =====================================================
    # 4. Update CRM Labels
    # =====================================================

    label_result = (
        sync_customer_labels(
            customer_no=
                customer_no,

            crm_labels=
                crm_payload[
                    "labels"
                ],
        )
    )


    # =====================================================
    # 5. Result
    # =====================================================

    success = (
        field_result.get(
            "success",
            False,
        )
        and
        label_result.get(
            "success",
            False,
        )
    )


    return {
        "success":
            success,

        "customerId":
            customer_id,

        "customerNo":
            customer_no,

        "fields":
            field_result,

        "labels":
            label_result,
    }