from datetime import datetime, timezone
from statistics import median

from history.constants import (
    HISTORY_TIMEZONE,
    RECENT_WINDOW_DAYS,
    TIME_DECAY_BASE,

    STATE_CATEGORIES,
    GOAL_CATEGORIES,
    GUIDANCE_CATEGORIES,
    INTENT_CATEGORIES,

    BAYESIAN_PRIOR_STRENGTH,

    SCENE_MAPPING,
    SCENE_CATEGORIES,
    SCENE_PREFERENCE_SCORE_MAPPING,

    BREATHING_MAPPING,
    BREATHING_CATEGORIES,

    TECHNIQUE_CATEGORIES,
)

from history.classifiers import (
    classify_recent_effect,
    classify_explore_score,
    classify_effect_level,
    classify_scene_preference,

    classify_preferred_duration,
    classify_usage_frequency,
    classify_completion,
)

# =========================================================
# Timestamp 工具
# =========================================================

def _ensure_datetime(value):
    """
    確保輸入是 timezone-aware datetime。

    Firestore Timestamp 透過 Firebase Admin 讀取後，
    通常本身就是 datetime。
    """

    if not isinstance(value, datetime):
        return None

    if value.tzinfo is None:
        value = value.replace(
            tzinfo=timezone.utc
        )

    return value


def _calendar_days_ago(
    timestamp: datetime,
    now: datetime | None = None,
) -> int | None:
    """
    依 Asia/Taipei 的「日曆日」計算距今天幾天。

    例如：
    今天 → 0
    昨天 → 1
    6 天前 → 6
    """

    timestamp = _ensure_datetime(
        timestamp
    )

    if timestamp is None:
        return None


    if now is None:
        now = datetime.now(
            HISTORY_TIMEZONE
        )
    else:
        now = _ensure_datetime(now)

        if now is None:
            return None

        now = now.astimezone(
            HISTORY_TIMEZONE
        )


    local_timestamp = (
        timestamp.astimezone(
            HISTORY_TIMEZONE
        )
    )


    days_ago = (
        now.date()
        - local_timestamp.date()
    ).days


    return days_ago


# =========================================================
# 時間衰減
# =========================================================

def _time_decay_weight(
    days_ago: int
) -> float:
    """
    w = 0.8 ^ d
    """

    return (
        TIME_DECAY_BASE
        ** days_ago
    )


def _calculate_recent_second_assessment_category(
    sessions: list[dict],
    field_name: str,
    categories: list[str],
    now: datetime | None = None,
) -> dict:
    """
    共用於：
    - recentState
    - recentGoal
    - recentGuidance

    使用：
    secondAssessment.submittedAt

    公式：
    Score(c)
    = Σ I(x_i = c) × 0.8 ^ d_i

    若最高分同分：
    → 取最近一次出現的類別
    """

    scores = {
        category: 0.0
        for category in categories
    }

    # 紀錄每個類別最近一次出現時間
    latest_seen = {
        category: None
        for category in categories
    }

    valid_count = 0


    for session in sessions:

        second_assessment = (
            session.get(
                "secondAssessment"
            )
        )


        if not isinstance(
            second_assessment,
            dict
        ):
            continue


        value = (
            second_assessment.get(
                field_name
            )
        )

        submitted_at = (
            second_assessment.get(
                "submittedAt"
            )
        )


        # =========================================
        # 檢查答案是否合法
        # =========================================

        if value not in categories:
            continue


        # =========================================
        # 檢查時間
        # =========================================

        submitted_at = (
            _ensure_datetime(
                submitted_at
            )
        )


        if submitted_at is None:
            continue


        days_ago = (
            _calendar_days_ago(
                submitted_at,
                now=now,
            )
        )


        if days_ago is None:
            continue


        # 最近 7 個日曆日
        # 今天 = 0
        # 6 天前 = 6
        if not (
            0
            <= days_ago
            < RECENT_WINDOW_DAYS
        ):
            continue


        # =========================================
        # 計算時間衰減
        # =========================================

        weight = (
            _time_decay_weight(
                days_ago
            )
        )


        scores[value] += weight

        valid_count += 1


        # =========================================
        # 紀錄這個類別最近一次出現時間
        # =========================================

        if (
            latest_seen[value] is None
            or
            submitted_at
            > latest_seen[value]
        ):
            latest_seen[value] = (
                submitted_at
            )


    # =========================================
    # 完全沒有有效資料
    # =========================================

    if valid_count == 0:

        rounded_scores = {
            key: round(value, 6)
            for key, value
            in scores.items()
        }

        return {
            "top": None,
            "scores": rounded_scores,
            "sampleCount": 0,
        }


    # =========================================
    # 找最高分
    # =========================================

    max_score = max(
        scores.values()
    )


    # =========================================
    # 找所有最高分的類別
    # =========================================

    tied_categories = [
        category
        for category, score
        in scores.items()
        if abs(score - max_score) < 1e-9
    ]


    # =========================================
    # 沒有同分
    # =========================================

    if len(tied_categories) == 1:

        top = tied_categories[0]


    # =========================================
    # 最高分同分
    # → 選最近一次出現的
    # =========================================

    else:

        top = max(
            tied_categories,
            key=lambda category:
                latest_seen[category]
        )


    # =========================================
    # 最後才 round
    # =========================================

    rounded_scores = {
        key: round(value, 6)
        for key, value
        in scores.items()
    }


    return {
        "top": top,
        "scores": rounded_scores,
        "sampleCount": valid_count,
    }


# =========================================================
# 1. Recent State
# =========================================================

def calculate_recent_state(
    sessions: list[dict],
    now: datetime | None = None,
) -> dict:

    return (
        _calculate_recent_second_assessment_category(
            sessions=sessions,
            field_name="currentState",
            categories=STATE_CATEGORIES,
            now=now,
        )
    )


# =========================================================
# 2. Recent Goal
# =========================================================

def calculate_recent_goal(
    sessions: list[dict],
    now: datetime | None = None,
) -> dict:

    return (
        _calculate_recent_second_assessment_category(
            sessions=sessions,
            field_name="desiredOutcome",
            categories=GOAL_CATEGORIES,
            now=now,
        )
    )


# =========================================================
# 3. Recent Guidance
# =========================================================

def calculate_recent_guidance(
    sessions: list[dict],
    now: datetime | None = None,
) -> dict:

    return (
        _calculate_recent_second_assessment_category(
            sessions=sessions,
            field_name="companionPreference",
            categories=GUIDANCE_CATEGORIES,
            now=now,
        )
    )

# =========================================================
# 4. Recent Effect
# =========================================================

def calculate_recent_effect(
    sessions: list[dict],
    now: datetime | None = None,
) -> dict:
    """
    最近 7 天 Post Q1 放鬆效果。

    EffectScore
    = Σ(score × weight)
      / Σ(weight)

    weight = 0.8 ^ days_ago
    """

    weighted_score_sum = 0.0

    weight_sum = 0.0

    valid_count = 0


    for session in sessions:

        third_assessment = (
            session.get(
                "thirdAssessment"
            )
        )


        if not isinstance(
            third_assessment,
            dict
        ):
            continue


        # =========================================
        # Post Q1
        # =========================================

        relaxation = (
            third_assessment.get(
                "relaxation"
            )
        )


        if not isinstance(
            relaxation,
            dict
        ):
            continue


        score = relaxation.get(
            "score"
        )


        if not isinstance(
            score,
            (int, float)
        ):
            continue


        score = float(score)


        # Post Q1 合法範圍 1 ~ 5
        if not 1 <= score <= 5:
            continue


        # =========================================
        # 使用第三份問卷 submittedAt
        # =========================================

        submitted_at = (
            third_assessment.get(
                "submittedAt"
            )
        )


        days_ago = (
            _calendar_days_ago(
                submitted_at,
                now=now,
            )
        )


        if days_ago is None:
            continue


        if not (
            0
            <= days_ago
            < RECENT_WINDOW_DAYS
        ):
            continue


        # =========================================
        # 時間權重
        # =========================================

        weight = (
            _time_decay_weight(
                days_ago
            )
        )


        weighted_score_sum += (
            score * weight
        )

        weight_sum += weight

        valid_count += 1


    # =========================================
    # 最近 7 天完全沒有 Post Q1
    # =========================================

    if valid_count == 0:
        return {
            "score": None,
            "level": None,
            "sampleCount": 0,
        }


    effect_score = (
        weighted_score_sum
        / weight_sum
    )


    effect_score = round(
        effect_score,
        6
    )


    return {
        "score": effect_score,

        "level":
            classify_recent_effect(
                effect_score
            ),

        "sampleCount":
            valid_count,
    }

# =========================================================
# 取得 Post Q3 key
# 同時支援新版 / 舊版 Firestore Schema
# =========================================================

def _get_reuse_intent_key(
    third_assessment: dict
) -> str | None:

    reuse_intent = (
        third_assessment.get(
            "reuseIntent"
        )
    )


    # =========================================
    # 新版
    #
    # reuseIntent: {
    #     score: ...,
    #     key: ...
    # }
    # =========================================

    if isinstance(
        reuse_intent,
        dict
    ):

        key = reuse_intent.get(
            "key"
        )

        if key in INTENT_CATEGORIES:
            return key


    # =========================================
    # 舊版
    #
    # reuseIntent: null
    # reuseIntentKey: "sleep_signal"
    # =========================================

    legacy_key = (
        third_assessment.get(
            "reuseIntentKey"
        )
    )


    if legacy_key in INTENT_CATEGORIES:
        return legacy_key


    return None

# =========================================================
# 5. Recent Intent
# =========================================================

def calculate_recent_intent(
    sessions: list[dict],
    now: datetime | None = None,
) -> dict:
    """
    最近 7 天 Post Q3 使用意願。

    IntentScore(k)
    = Σ I(x = k) × 0.8^d

    若最高分同分：
    → 最近一次回答優先
    """

    scores = {
        category: 0.0
        for category
        in INTENT_CATEGORIES
    }


    latest_seen = {
        category: None
        for category
        in INTENT_CATEGORIES
    }


    valid_count = 0


    for session in sessions:

        third_assessment = (
            session.get(
                "thirdAssessment"
            )
        )


        if not isinstance(
            third_assessment,
            dict
        ):
            continue


        intent_key = (
            _get_reuse_intent_key(
                third_assessment
            )
        )


        if intent_key is None:
            continue


        submitted_at = (
            _ensure_datetime(
                third_assessment.get(
                    "submittedAt"
                )
            )
        )


        if submitted_at is None:
            continue


        days_ago = (
            _calendar_days_ago(
                submitted_at,
                now=now,
            )
        )


        if days_ago is None:
            continue


        if not (
            0
            <= days_ago
            < RECENT_WINDOW_DAYS
        ):
            continue


        weight = (
            _time_decay_weight(
                days_ago
            )
        )


        scores[intent_key] += (
            weight
        )

        valid_count += 1


        # 最近出現時間
        if (
            latest_seen[intent_key]
            is None
            or
            submitted_at
            > latest_seen[intent_key]
        ):
            latest_seen[intent_key] = (
                submitted_at
            )


    # =========================================
    # 無資料
    # =========================================

    if valid_count == 0:

        return {
            "top": None,

            "scores": {
                key: round(value, 6)
                for key, value
                in scores.items()
            },

            "sampleCount": 0,
        }


    # =========================================
    # 找最高分
    # =========================================

    max_score = max(
        scores.values()
    )


    tied_categories = [
        category

        for category, score
        in scores.items()

        if abs(
            score - max_score
        ) < 1e-9
    ]


    # =========================================
    # Tie-break
    # =========================================

    if len(tied_categories) == 1:

        top = tied_categories[0]

    else:

        top = max(
            tied_categories,
            key=lambda category:
                latest_seen[category]
        )


    rounded_scores = {
        key: round(value, 6)

        for key, value
        in scores.items()
    }


    return {
        "top": top,
        "scores": rounded_scores,
        "sampleCount": valid_count,
    }

# =========================================================
# 6. Explore Score
# =========================================================

def calculate_explore_score(
    sessions: list[dict],
    now: datetime | None = None,
) -> dict:

    explore_weight_sum = 0.0

    valid_weight_sum = 0.0

    valid_count = 0

    sleep_signal_count = 0


    for session in sessions:

        third_assessment = (
            session.get(
                "thirdAssessment"
            )
        )


        if not isinstance(
            third_assessment,
            dict
        ):
            continue


        intent_key = (
            _get_reuse_intent_key(
                third_assessment
            )
        )


        if intent_key is None:
            continue


        submitted_at = (
            third_assessment.get(
                "submittedAt"
            )
        )


        days_ago = (
            _calendar_days_ago(
                submitted_at,
                now=now,
            )
        )


        if days_ago is None:
            continue


        if not (
            0
            <= days_ago
            < RECENT_WINDOW_DAYS
        ):
            continue


        # =========================================
        # sleep_signal 不納入 ExploreScore
        # =========================================

        if intent_key == "sleep_signal":

            sleep_signal_count += 1

            continue


        # =========================================
        # 只剩 explore / reuse
        # =========================================

        weight = (
            _time_decay_weight(
                days_ago
            )
        )


        valid_weight_sum += (
            weight
        )

        valid_count += 1


        if (
            intent_key
            == "explore_other"
        ):

            explore_weight_sum += (
                weight
            )


    # =========================================
    # 完全沒有 Explore / Reuse 資料
    # =========================================

    if valid_count == 0:

        return {
            "score": None,
            "level": None,
            "sampleCount": 0,
            "sleepSignalCount":
                sleep_signal_count,
        }


    explore_score = (
        explore_weight_sum
        / valid_weight_sum
    )


    explore_score = round(
        explore_score,
        6
    )


    return {
        "score":
            explore_score,

        "level":
            classify_explore_score(
                explore_score
            ),

        "sampleCount":
            valid_count,

        "sleepSignalCount":
            sleep_signal_count,
    }

# =========================================================
# 7. Scene Preference
# =========================================================

def calculate_scene_preference(
    sessions: list[dict],
    now: datetime | None = None,
) -> dict:
    """
    ScenePreference(s)
    = (Σr + mμ) / (n + m)

    Post Q2 採 1~5 分：
    very_dislike = 1
    dislike      = 2
    okay         = 3
    like         = 4
    very_like    = 5
    """

    scene_scores = {
        scene: []
        for scene in SCENE_CATEGORIES
    }

    all_scores = []


    for session in sessions:

        # =========================================
        # Scene
        # =========================================

        scene = _get_scene_key(
            session
        )

        if scene not in SCENE_CATEGORIES:
            continue


        # =========================================
        # Third Assessment
        # =========================================

        third_assessment = (
            session.get(
                "thirdAssessment"
            )
        )

        if not isinstance(
            third_assessment,
            dict
        ):
            continue


        # =========================================
        # Post Q2
        # =========================================

        scene_preference = (
            third_assessment.get(
                "scenePreference"
            )
        )

        if not isinstance(
            scene_preference,
            dict
        ):
            continue


        preference_key = (
            scene_preference.get(
                "key"
            )
        )


        # 以 key 為正式依據
        score = (
            SCENE_PREFERENCE_SCORE_MAPPING.get(
                preference_key
            )
        )


        if score is None:
            continue


        # =========================================
        # 最近 7 天
        # =========================================

        submitted_at = (
            third_assessment.get(
                "submittedAt"
            )
        )

        days_ago = (
            _calendar_days_ago(
                submitted_at,
                now=now,
            )
        )

        if days_ago is None:
            continue

        if not (
            0
            <= days_ago
            < RECENT_WINDOW_DAYS
        ):
            continue


        scene_scores[
            scene
        ].append(
            float(score)
        )

        all_scores.append(
            float(score)
        )


    # =========================================
    # 完全沒有 Post Q2
    # =========================================

    if len(all_scores) == 0:

        return {
            "priorMean": None,

            "items": {
                scene: {
                    "preference": None,
                    "level": None,
                    "sampleCount": 0,
                    "hasData": False,
                    "isPositivePreference": False,
                    "isHighlyPositivePreference": False,
                }

                for scene
                in SCENE_CATEGORIES
            },

            "positivePreferenceScenes": [],
            "highPreferenceScenes": [],
        }


    # =========================================
    # μ：最近 7 天全部 Scene 的平均喜好
    # =========================================

    prior_mean = (
        sum(all_scores)
        / len(all_scores)
    )


    items = {}

    positive_scenes = []

    high_preference_scenes = []


    for scene in SCENE_CATEGORIES:

        scores = (
            scene_scores[
                scene
            ]
        )

        n = len(scores)


        preference = (
            sum(scores)
            +
            BAYESIAN_PRIOR_STRENGTH
            * prior_mean
        ) / (
            n
            +
            BAYESIAN_PRIOR_STRENGTH
        )


        preference = round(
            preference,
            6
        )


        has_data = (
            n > 0
        )


        # =========================================
        # 只有實際使用過才標記偏好
        # =========================================

        is_positive = (
            has_data
            and
            preference >= 3.41
        )

        is_high = (
            has_data
            and
            preference >= 4.21
        )


        items[scene] = {
            "preference":
                preference,

            "level":
                (
                    classify_scene_preference(
                        preference
                    )
                    if has_data
                    else None
                ),

            "sampleCount":
                n,

            "hasData":
                has_data,

            "isPositivePreference":
                is_positive,

            "isHighlyPositivePreference":
                is_high,
        }


        if is_positive:
            positive_scenes.append(
                scene
            )

        if is_high:
            high_preference_scenes.append(
                scene
            )


    return {
        "priorMean":
            round(
                prior_mean,
                6
            ),

        "items":
            items,

        "positivePreferenceScenes":
            positive_scenes,

        "highPreferenceScenes":
            high_preference_scenes,
    }

# =========================================================
# Bayesian Effect 共用計算器
# =========================================================

def _calculate_bayesian_effect_by_group(
    sessions: list[dict],
    categories: list[str],
    group_getter,
    now: datetime | None = None,
) -> dict:
    """
    共用於：

    - SceneEffect
    - BreathingEffect
    - TechniqueEffect
    - GuidanceEffect

    Effect(c)
    = (Σr + mμ) / (n + m)

    μ：
    最近 7 天所有符合條件紀錄的
    Post Q1 整體平均。

    m：
    Bayesian prior strength，預設 2。
    """

    # 每一類的 Post Q1
    group_scores = {
        category: []
        for category in categories
    }

    # 所有有效 Post Q1
    all_scores = []


    for session in sessions:

        # =========================================
        # 第三份問卷
        # =========================================

        third_assessment = (
            session.get(
                "thirdAssessment"
            )
        )

        if not isinstance(
            third_assessment,
            dict
        ):
            continue


        # =========================================
        # Post Q1
        # =========================================

        relaxation = (
            third_assessment.get(
                "relaxation"
            )
        )

        if not isinstance(
            relaxation,
            dict
        ):
            continue


        score = relaxation.get(
            "score"
        )

        if not isinstance(
            score,
            (int, float)
        ):
            continue


        score = float(score)

        if not 1 <= score <= 5:
            continue


        # =========================================
        # 以 Post submittedAt 判斷最近 7 天
        # =========================================

        submitted_at = (
            third_assessment.get(
                "submittedAt"
            )
        )

        days_ago = (
            _calendar_days_ago(
                submitted_at,
                now=now,
            )
        )

        if days_ago is None:
            continue

        if not (
            0
            <= days_ago
            < RECENT_WINDOW_DAYS
        ):
            continue


        # =========================================
        # 取得這筆 Session 所屬類別
        # =========================================

        category = group_getter(
            session
        )

        if category not in categories:
            continue


        group_scores[category].append(
            score
        )

        all_scores.append(
            score
        )


    # =========================================
    # 完全沒有 Post Q1
    # =========================================

    if len(all_scores) == 0:

        return {
            "priorMean": None,

            "items": {
                category: {
                    "effect": None,
                    "sampleCount": 0,
                    "hasData": False,
                }

                for category
                in categories
            }
        }


    # =========================================
    # μ：整體平均 Post Q1
    # =========================================

    prior_mean = (
        sum(all_scores)
        / len(all_scores)
    )


    results = {}


    for category in categories:

        scores = (
            group_scores[
                category
            ]
        )

        n = len(scores)


        # =========================================
        # Bayesian Shrinkage
        #
        # 即使 n = 0，
        # effect 也會回到 prior mean。
        # =========================================

        effect = (
            sum(scores)
            +
            BAYESIAN_PRIOR_STRENGTH
            * prior_mean
        ) / (
            n
            +
            BAYESIAN_PRIOR_STRENGTH
        )


        results[category] = {
            "effect":
                round(
                    effect,
                    6
                ),

            "sampleCount":
                n,

            "hasData":
                n > 0,
        }


    return {
        "priorMean":
            round(
                prior_mean,
                6
            ),

        "items":
            results,
    }

def _get_scene_key(
    session: dict
) -> str | None:

    raw_scene = session.get(
        "sceneName"
    )

    return SCENE_MAPPING.get(
        raw_scene
    )

# =========================================================
# 8. Scene Effect
# =========================================================

def calculate_scene_effect(
    sessions: list[dict],
    now: datetime | None = None,
) -> dict:

    effect_result = (
        _calculate_bayesian_effect_by_group(
            sessions=sessions,
            categories=SCENE_CATEGORIES,
            group_getter=_get_scene_key,
            now=now,
        )
    )


    # =========================================
    # 每個 Scene 的完成率
    # =========================================

    completion_values = {
        category: []
        for category
        in SCENE_CATEGORIES
    }


    for session in sessions:

        scene = _get_scene_key(
            session
        )

        if scene not in SCENE_CATEGORIES:
            continue


        # 使用 Session startTime 判斷最近 7 天
        start_time = session.get(
            "startTime"
        )

        days_ago = (
            _calendar_days_ago(
                start_time,
                now=now,
            )
        )

        if days_ago is None:
            continue

        if not (
            0
            <= days_ago
            < RECENT_WINDOW_DAYS
        ):
            continue


        actual_seconds = (
            session.get(
                "actualDurationSeconds"
            )
        )

        planned_minutes = (
            session.get(
                "plannedDurationMinutes"
            )
        )


        if not isinstance(
            actual_seconds,
            (int, float)
        ):
            continue

        if not isinstance(
            planned_minutes,
            (int, float)
        ):
            continue

        if planned_minutes <= 0:
            continue


        planned_seconds = (
            float(planned_minutes)
            * 60.0
        )


        completion_rate = min(
            float(actual_seconds)
            / planned_seconds,
            1.0
        )


        completion_values[
            scene
        ].append(
            completion_rate
        )


    high_effect_scenes = []


    for scene in SCENE_CATEGORIES:

        rates = (
            completion_values[
                scene
            ]
        )


        if len(rates) > 0:

            avg_completion = (
                sum(rates)
                / len(rates)
            )

        else:

            avg_completion = None


        item = (
            effect_result[
                "items"
            ][scene]
        )


        item[
            "avgCompletionRate"
        ] = (
            None
            if avg_completion is None
            else round(
                avg_completion,
                6
            )
        )


        item[
            "completionSampleCount"
        ] = len(rates)


        # =========================================
        # 高效果場景
        #
        # 一定要實際有 Post Q1，
        # 不能只靠 priorMean。
        # =========================================

        is_high_effect = (
            item["hasData"]
            and
            item["effect"] >= 3.41
            and
            avg_completion is not None
            and
            avg_completion >= 0.75
        )


        item[
            "isHighEffect"
        ] = is_high_effect


        if is_high_effect:

            high_effect_scenes.append(
                scene
            )


    effect_result[
        "highEffectScenes"
    ] = high_effect_scenes


    return effect_result

def _get_breathing_key(
    session: dict
) -> str | None:

    raw_breathing = (
        session.get(
            "breathingMode"
        )
    )

    return BREATHING_MAPPING.get(
        raw_breathing
    )

# =========================================================
# 9. Breathing Effect
# =========================================================

def calculate_breathing_effect(
    sessions: list[dict],
    now: datetime | None = None,
) -> dict:

    result = (
        _calculate_bayesian_effect_by_group(
            sessions=sessions,
            categories=BREATHING_CATEGORIES,
            group_getter=_get_breathing_key,
            now=now,
        )
    )


    high_effect_breathings = []


    for breathing, item in (
        result["items"].items()
    ):

        effect = item[
            "effect"
        ]


        item["level"] = (
            classify_effect_level(
                effect
            )
            if item["hasData"]
            else None
        )


        item["history"] = (
            round(
                (effect - 1.0)
                / 4.0,
                6
            )
            if (
                item["hasData"]
                and effect is not None
            )
            else None
        )


        if (
            item["hasData"]
            and effect >= 3.41
        ):
            high_effect_breathings.append(
                breathing
            )


    result[
        "highEffectBreathings"
    ] = high_effect_breathings


    return result

def _get_technique_key(
    session: dict
) -> str | None:

    technique = (
        session.get(
            "technique"
        )
    )

    if (
        technique
        in TECHNIQUE_CATEGORIES
    ):
        return technique

    return None

# =========================================================
# 10. Technique Effect
# =========================================================

def calculate_technique_effect(
    sessions: list[dict],
    now: datetime | None = None,
) -> dict:

    result = (
        _calculate_bayesian_effect_by_group(
            sessions=sessions,
            categories=TECHNIQUE_CATEGORIES,
            group_getter=_get_technique_key,
            now=now,
        )
    )


    high_effect_techniques = []


    for technique, item in (
        result["items"].items()
    ):

        effect = item[
            "effect"
        ]


        item["level"] = (
            classify_effect_level(
                effect
            )
            if item["hasData"]
            else None
        )


        # =========================================
        # Technique History
        #
        # 1~5 → 0~1
        # =========================================

        item["history"] = (
            round(
                (effect - 1.0)
                / 4.0,
                6
            )
            if (
                item["hasData"]
                and effect is not None
            )
            else None
        )


        if (
            item["hasData"]
            and effect >= 3.41
        ):
            high_effect_techniques.append(
                technique
            )


    result[
        "highEffectTechniques"
    ] = high_effect_techniques


    return result

def _get_guidance_key(
    session: dict
) -> str | None:

    second_assessment = (
        session.get(
            "secondAssessment"
        )
    )

    if not isinstance(
        second_assessment,
        dict
    ):
        return None


    guidance = (
        second_assessment.get(
            "companionPreference"
        )
    )


    if (
        guidance
        in GUIDANCE_CATEGORIES
    ):
        return guidance


    return None

def _get_applied_guidance_key(
    session: dict,
) -> str | None:
    """
    取得這個 Session 實際使用的 Guidance。

    優先：
    1. resolvedGuidanceHistoryKey
       → 系統已明確記錄實際採用 Guidance
    2. companionPreference
       → 使用者本次明確選擇

    回傳 History 使用的 key：
    gentle_companion
    guided_relaxation
    ambient_only
    quiet_with_encouragement
    """

    second_assessment = (
        session.get(
            "secondAssessment"
        )
    )

    if not isinstance(
        second_assessment,
        dict
    ):
        return None


    # =========================================
    # 1. 實際套用的 Guidance
    # =========================================

    resolved_key = (
        second_assessment.get(
            "resolvedGuidanceHistoryKey"
        )
    )

    if (
        isinstance(
            resolved_key,
            str
        )
        and resolved_key
        in GUIDANCE_CATEGORIES
    ):
        return resolved_key


    # =========================================
    # 2. 使用者明確選擇
    # =========================================

    explicit_key = (
        second_assessment.get(
            "companionPreference"
        )
    )

    if (
        isinstance(
            explicit_key,
            str
        )
        and explicit_key
        in GUIDANCE_CATEGORIES
    ):
        return explicit_key


    return None

# =========================================================
# 11. Guidance Effect + Guide Rank
# =========================================================

def calculate_guidance_effect(
    sessions: list[dict],
    now: datetime | None = None,
) -> dict:
    """
    GuidanceEffect：
    Bayesian Shrinkage

    GuideRank：
    0.40 × PreferenceNorm
    + 0.60 × EffectNorm

    不另外輸出 guideRank，
    直接整合至 guidanceEffect。
    """

    # =========================================
    # 1. Bayesian Guidance Effect
    # =========================================

    result = (
        _calculate_bayesian_effect_by_group(
            sessions=sessions,
            categories=GUIDANCE_CATEGORIES,
            group_getter=_get_applied_guidance_key,
            now=now,
        )
    )


    # =========================================
    # 2. 最近 Guidance Preference
    # =========================================

    recent_guidance = (
        calculate_recent_guidance(
            sessions,
            now=now,
        )
    )

    preference_scores = (
        recent_guidance[
            "scores"
        ]
    )


    total_preference = sum(
        preference_scores.values()
    )


    # =========================================
    # 3. 計算每種 Guidance Rank
    # =========================================

    for guidance in GUIDANCE_CATEGORIES:

        item = (
            result[
                "items"
            ][guidance]
        )


        preference_score = (
            preference_scores.get(
                guidance,
                0.0
            )
        )


        # -----------------------------------------
        # Preference → 0~1
        # -----------------------------------------

        if total_preference > 0:

            preference_norm = (
                preference_score
                / total_preference
            )

        else:

            preference_norm = None


        # -----------------------------------------
        # Effect → 0~1
        # -----------------------------------------

        effect = (
            item[
                "effect"
            ]
        )


        if effect is not None:

            effect_norm = (
                effect - 1.0
            ) / 4.0

        else:

            effect_norm = None


        # -----------------------------------------
        # GuideRank
        # -----------------------------------------

        if (
            preference_norm is not None
            and
            effect_norm is not None
        ):

            rank = (
                0.40
                * preference_norm
                +
                0.60
                * effect_norm
            )

        else:

            rank = None


        # -----------------------------------------
        # 寫回同一個 item
        # -----------------------------------------

        item[
            "preferenceScore"
        ] = round(
            preference_score,
            6
        )


        item[
            "preferenceNorm"
        ] = (
            None
            if preference_norm is None
            else round(
                preference_norm,
                6
            )
        )


        item[
            "effectNorm"
        ] = (
            None
            if effect_norm is None
            else round(
                effect_norm,
                6
            )
        )


        item[
            "rank"
        ] = (
            None
            if rank is None
            else round(
                rank,
                6
            )
        )


        item[
            "level"
        ] = (
            classify_effect_level(
                effect
            )
            if item["hasData"]
            else None
        )


    # =========================================
    # 4. High Effect Guidance
    #
    # 必須：
    # - 真正有 Post Q1
    # - GuidanceEffect >= 3.41
    #
    # 再按照 GuideRank 排序
    # =========================================

    high_effect_guidances = [
        guidance

        for guidance
        in GUIDANCE_CATEGORIES

        if (
            result["items"][
                guidance
            ]["hasData"]

            and

            result["items"][
                guidance
            ]["effect"]
            >= 3.41
        )
    ]


    high_effect_guidances.sort(
        key=lambda guidance:
            (
                result["items"][
                    guidance
                ]["rank"]
                or 0
            ),
        reverse=True,
    )


    result[
        "highEffectGuidances"
    ] = (
        high_effect_guidances
    )


    return result

# =========================================================
# Session 共用工具
# =========================================================

def _is_actual_meditation_session(
    session: dict
) -> bool:
    """
    判斷是否真的有進行冥想。

    Session 在 Pre Questionnaire 後就可能先建立，
    因此不能只看 document 是否存在。

    目前以 actualDurationSeconds > 0
    判定使用者真的有進行冥想。
    """

    actual_seconds = (
        session.get(
            "actualDurationSeconds"
        )
    )

    return (
        isinstance(
            actual_seconds,
            (int, float)
        )
        and
        actual_seconds > 0
    )


def _get_completion_rate(
    session: dict
) -> float | None:

    actual_seconds = (
        session.get(
            "actualDurationSeconds"
        )
    )

    planned_minutes = (
        session.get(
            "plannedDurationMinutes"
        )
    )


    if not isinstance(
        actual_seconds,
        (int, float)
    ):
        return None


    if not isinstance(
        planned_minutes,
        (int, float)
    ):
        return None


    if planned_minutes <= 0:
        return None


    planned_seconds = (
        float(planned_minutes)
        * 60.0
    )


    return min(
        float(actual_seconds)
        / planned_seconds,
        1.0
    )

# =========================================================
# 12. Preferred Duration
# =========================================================

def calculate_preferred_duration(
    sessions: list[dict],
    now: datetime | None = None,
) -> dict:

    durations_minutes = []


    for session in sessions:

        if not _is_actual_meditation_session(
            session
        ):
            continue


        start_time = (
            session.get(
                "startTime"
            )
        )


        days_ago = (
            _calendar_days_ago(
                start_time,
                now=now,
            )
        )


        if days_ago is None:
            continue


        if not (
            0
            <= days_ago
            < RECENT_WINDOW_DAYS
        ):
            continue


        actual_seconds = float(
            session[
                "actualDurationSeconds"
            ]
        )


        durations_minutes.append(
            actual_seconds / 60.0
        )


    if len(
        durations_minutes
    ) == 0:

        return {
            "minutes": None,
            "level": None,
            "sampleCount": 0,
        }


    preferred_minutes = median(
        durations_minutes
    )


    preferred_minutes = round(
        preferred_minutes,
        2
    )


    return {
        "minutes":
            preferred_minutes,

        "level":
            classify_preferred_duration(
                preferred_minutes
            ),

        "sampleCount":
            len(
                durations_minutes
            ),
    }

# =========================================================
# 13. Usage Frequency
# =========================================================

def calculate_usage_frequency(
    sessions: list[dict],
    now: datetime | None = None,
) -> dict:

    count_7d = 0
    count_28d = 0


    for session in sessions:

        if not _is_actual_meditation_session(
            session
        ):
            continue


        start_time = (
            session.get(
                "startTime"
            )
        )


        days_ago = (
            _calendar_days_ago(
                start_time,
                now=now,
            )
        )


        if days_ago is None:
            continue


        if (
            0
            <= days_ago
            < 28
        ):

            count_28d += 1


        if (
            0
            <= days_ago
            < 7
        ):

            count_7d += 1


    weekly_average_28d = (
        count_28d
        / 4.0
    )


    return {
        "count7d":
            count_7d,

        "count28d":
            count_28d,

        "weeklyAverage28d":
            round(
                weekly_average_28d,
                2
            ),

        "level":
            classify_usage_frequency(
                count_7d
            ),
    }

# =========================================================
# 14. Completion
# =========================================================

def calculate_completion(
    sessions: list[dict],
    now: datetime | None = None,
) -> dict:

    completion_rates = []


    for session in sessions:

        if not _is_actual_meditation_session(
            session
        ):
            continue


        start_time = (
            session.get(
                "startTime"
            )
        )


        days_ago = (
            _calendar_days_ago(
                start_time,
                now=now,
            )
        )


        if days_ago is None:
            continue


        if not (
            0
            <= days_ago
            < RECENT_WINDOW_DAYS
        ):
            continue


        completion_rate = (
            _get_completion_rate(
                session
            )
        )


        if completion_rate is None:
            continue


        completion_rates.append(
            completion_rate
        )


    if len(
        completion_rates
    ) == 0:

        return {
            "rate": None,
            "level": None,
            "sampleCount": 0,
        }


    completion_median = median(
        completion_rates
    )


    completion_median = round(
        completion_median,
        6
    )


    return {
        "rate":
            completion_median,

        "level":
            classify_completion(
                completion_median
            ),

        "sampleCount":
            len(
                completion_rates
            ),
    }

# =========================================================
# 15. Preferred Time
# =========================================================

def calculate_preferred_time(
    sessions: list[dict],
    now: datetime | None = None,
) -> dict:

    counts = {
        "morning": 0,
        "daytime": 0,
        "evening": 0,
        "late_night": 0,
    }


    for session in sessions:

        if not _is_actual_meditation_session(
            session
        ):
            continue


        start_time = (
            _ensure_datetime(
                session.get(
                    "startTime"
                )
            )
        )


        if start_time is None:
            continue


        days_ago = (
            _calendar_days_ago(
                start_time,
                now=now,
            )
        )


        if days_ago is None:
            continue


        if not (
            0
            <= days_ago
            < 28
        ):
            continue


        local_time = (
            start_time.astimezone(
                HISTORY_TIMEZONE
            )
        )


        hour = (
            local_time.hour
        )


        if (
            5
            <= hour
            < 11
        ):

            period = "morning"


        elif (
            11
            <= hour
            < 17
        ):

            period = "daytime"


        elif (
            17
            <= hour
            < 23
        ):

            period = "evening"


        else:

            period = "late_night"


        counts[
            period
        ] += 1


    total = sum(
        counts.values()
    )


    if total == 0:

        return {
            "primary": [],
            "type": None,

            "ratios": {
                period: 0.0
                for period
                in counts
            },

            "sampleCount": 0,
        }


    ratios = {
        period:
            count / total

        for period, count
        in counts.items()
    }


    # =========================================
    # 判斷是否完全均勻
    # =========================================

    ratio_values = list(
        ratios.values()
    )


    is_uniform = (
        max(ratio_values)
        -
        min(ratio_values)
        < 1e-9
    )


    if is_uniform:

        primary = []

        preference_type = (
            "flexible"
        )


    else:

        # 由高到低排序
        sorted_periods = sorted(
            ratios,
            key=ratios.get,
            reverse=True,
        )


        primary = [
            period

            for period
            in sorted_periods

            if ratios[
                period
            ] >= 0.25
        ][:2]


        preference_type = (
            "habitual"
            if len(primary) > 0
            else "flexible"
        )


    rounded_ratios = {
        period:
            round(
                ratio,
                6
            )

        for period, ratio
        in ratios.items()
    }


    return {
        "primary":
            primary,

        "type":
            preference_type,

        "ratios":
            rounded_ratios,

        "sampleCount":
            total,
    }