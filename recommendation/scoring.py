# ==========================================================
# Recommendation Scoring
# 尚未納入 History 的冷啟動推薦分數
#
# Score =
# 0.40 * StateFit
# + 0.30 * GoalFit
# + 0.30 * BaselineFit
# ==========================================================


STATE_WEIGHT = 0.40
GOAL_WEIGHT = 0.30

# Cold Start
COLD_START_BASELINE_WEIGHT = 0.30

# 有 History 後
HISTORY_BASELINE_WEIGHT = 0.10
HISTORY_WEIGHT = 0.20


def rank_candidates_without_history(
    state: str,
    goal: str,
    baseline_ranking: list,
    state_matrix: dict,
    goal_matrix: dict,
) -> list:
    """
    根據：
    - Current State
    - Current Goal
    - BaselineFit

    計算尚未納入 History 時的候選排名。
    """

    # ------------------------------------------
    # 1. 檢查 State
    # ------------------------------------------

    if state not in state_matrix:
        raise ValueError(
            f"State Matrix 中不存在 state：{state}"
        )

    # ------------------------------------------
    # 2. 檢查 Goal
    # ------------------------------------------

    if goal not in goal_matrix:
        raise ValueError(
            f"Goal Matrix 中不存在 goal：{goal}"
        )

    # ------------------------------------------
    # 3. Baseline Ranking
    #    list -> dict
    #
    # [
    #   {"id": "ocean", "baselineFit": 0.9}
    # ]
    #
    # 轉成：
    #
    # {
    #   "ocean": 0.9
    # }
    # ------------------------------------------

    baseline_scores = {
        item["id"]: item["baselineFit"]
        for item in baseline_ranking
    }

    results = []

    # ------------------------------------------
    # 4. 計算所有候選
    # ------------------------------------------

    for candidate_id in state_matrix[state]:

        if candidate_id not in goal_matrix[goal]:
            raise ValueError(
                f"Goal Matrix 缺少候選：{candidate_id}"
            )

        if candidate_id not in baseline_scores:
            raise ValueError(
                f"Baseline Ranking 缺少候選：{candidate_id}"
            )

        state_fit = (
            state_matrix[state][candidate_id]
        )

        goal_fit = (
            goal_matrix[goal][candidate_id]
        )

        baseline_fit = (
            baseline_scores[candidate_id]
        )

        # --------------------------------------
        # Cold Start Score
        # --------------------------------------

        score = (
            STATE_WEIGHT * state_fit
            + GOAL_WEIGHT * goal_fit
            + COLD_START_BASELINE_WEIGHT * baseline_fit
        )

        results.append({
            "id": candidate_id,

            "stateFit":
                round(state_fit, 4),

            "goalFit":
                round(goal_fit, 4),

            "baselineFit":
                round(baseline_fit, 4),

            "score":
                round(score, 4),
        })

    # ------------------------------------------
    # 5. 分數高到低
    # ------------------------------------------

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results

# =========================================================
# Technique History
# =========================================================

def get_technique_history_score(
    technique: str,
    history_snapshot: dict | None,
) -> float | None:
    """
    回傳 Technique History，範圍 0~1。

    優先順序：

    1. 此 Technique 有真實個人 history
    2. 沒使用過 → 使用 Bayesian priorMean
    3. 完全沒有 History → None
    """

    if not isinstance(
        history_snapshot,
        dict
    ):
        return None


    technique_effect = (
        history_snapshot.get(
            "techniqueEffect"
        )
    )


    if not isinstance(
        technique_effect,
        dict
    ):
        return None


    items = (
        technique_effect.get(
            "items"
        )
    )


    if not isinstance(
        items,
        dict
    ):
        return None


    item = items.get(
        technique
    )


    # =========================================
    # 1. 此 Technique 有真實 History
    # =========================================

    if isinstance(
        item,
        dict
    ):

        history = item.get(
            "history"
        )

        if isinstance(
            history,
            (int, float)
        ):
            return float(history)


    # =========================================
    # 2. 沒實際使用過
    #
    # 使用 Bayesian priorMean
    # 1~5 → 0~1
    # =========================================

    prior_mean = (
        technique_effect.get(
            "priorMean"
        )
    )


    if isinstance(
        prior_mean,
        (int, float)
    ):

        prior_history = (
            float(prior_mean)
            - 1.0
        ) / 4.0


        return max(
            0.0,
            min(
                prior_history,
                1.0
            )
        )


    # =========================================
    # 3. 完全沒有歷史資料
    # =========================================

    return None

# =========================================================
# Technique Recommendation Score
# =========================================================

def calculate_technique_score(
    technique: str,
    state_fit: float,
    goal_fit: float,
    baseline_fit: float,
    history_snapshot: dict | None,
) -> dict:
    """
    計算單一 Technique 的推薦分數。

    完全沒有 History：
    0.40 State
    + 0.30 Goal
    + 0.30 Baseline

    有 History：
    0.40 State
    + 0.30 Goal
    + 0.10 Baseline
    + 0.20 History
    """

    history_fit = (
        get_technique_history_score(
            technique=technique,
            history_snapshot=history_snapshot,
        )
    )


    # =========================================
    # Cold Start
    # =========================================

    if history_fit is None:

        score = (
            STATE_WEIGHT * state_fit
            +
            GOAL_WEIGHT * goal_fit
            +
            COLD_START_BASELINE_WEIGHT
            * baseline_fit
        )


        return {
            "score":
                round(score, 4),

            "stateFit":
                round(state_fit, 4),

            "goalFit":
                round(goal_fit, 4),

            "baselineFit":
                round(baseline_fit, 4),

            "historyFit":
                None,

            "mode":
                "cold_start",
        }


    # =========================================
    # History Mode
    # =========================================

    score = (
        STATE_WEIGHT * state_fit
        +
        GOAL_WEIGHT * goal_fit
        +
        HISTORY_BASELINE_WEIGHT
        * baseline_fit
        +
        HISTORY_WEIGHT
        * history_fit
    )


    return {
        "score":
            round(score, 4),

        "stateFit":
            round(state_fit, 4),

        "goalFit":
            round(goal_fit, 4),

        "baselineFit":
            round(baseline_fit, 4),

        "historyFit":
            round(history_fit, 4),

        "mode":
            "history",
    }

# =========================================================
# Technique Ranking with History
# =========================================================

def rank_technique_candidates(
    state: str,
    goal: str,
    baseline_ranking: list,
    state_matrix: dict,
    goal_matrix: dict,
    history_snapshot: dict | None,
) -> list:
    """
    Technique 專用 Ranking。

    - 沒有 History → Cold Start
    - 有 History → 納入 Technique History
    """

    # =========================================
    # 1. 檢查 State
    # =========================================

    if state not in state_matrix:
        raise ValueError(
            f"State Matrix 中不存在 state：{state}"
        )


    # =========================================
    # 2. 檢查 Goal
    # =========================================

    if goal not in goal_matrix:
        raise ValueError(
            f"Goal Matrix 中不存在 goal：{goal}"
        )


    # =========================================
    # 3. Baseline Ranking
    #
    # list → dict
    # =========================================

    baseline_scores = {
        item["id"]:
            item["baselineFit"]

        for item
        in baseline_ranking
    }


    results = []


    # =========================================
    # 4. 計算六種 Technique
    # =========================================

    for technique in state_matrix[state]:

        if technique not in goal_matrix[goal]:
            raise ValueError(
                f"Goal Matrix 缺少 Technique："
                f"{technique}"
            )


        if technique not in baseline_scores:
            raise ValueError(
                f"Baseline Ranking 缺少 Technique："
                f"{technique}"
            )


        state_fit = (
            state_matrix[
                state
            ][technique]
        )


        goal_fit = (
            goal_matrix[
                goal
            ][technique]
        )


        baseline_fit = (
            baseline_scores[
                technique
            ]
        )


        # =====================================
        # Technique Score
        # =====================================

        score_result = (
            calculate_technique_score(
                technique=technique,
                state_fit=state_fit,
                goal_fit=goal_fit,
                baseline_fit=baseline_fit,
                history_snapshot=
                    history_snapshot,
            )
        )


        results.append({
            "id":
                technique,

            **score_result,
        })


    # =========================================
    # 5. 高分 → 低分
    # =========================================

    results.sort(
        key=lambda item:
            item["score"],
        reverse=True,
    )


    return results

# =========================================================
# Breathing History
# =========================================================

def get_breathing_history_score(
    breathing: str,
    history_snapshot: dict | None,
) -> float | None:
    """
    回傳 Breathing History，範圍 0~1。

    優先順序：

    1. 此 Breathing 有真實個人 history
    2. 沒使用過 → 使用 Bayesian priorMean
    3. 完全沒有 History → None
    """

    if not isinstance(
        history_snapshot,
        dict
    ):
        return None


    breathing_effect = (
        history_snapshot.get(
            "breathingEffect"
        )
    )


    if not isinstance(
        breathing_effect,
        dict
    ):
        return None


    items = (
        breathing_effect.get(
            "items"
        )
    )


    if not isinstance(
        items,
        dict
    ):
        return None


    item = items.get(
        breathing
    )


    # =========================================
    # 1. 此 Breathing 有真實 History
    # =========================================

    if isinstance(
        item,
        dict
    ):

        history = item.get(
            "history"
        )

        if isinstance(
            history,
            (int, float)
        ):
            return float(history)


    # =========================================
    # 2. 沒實際使用過
    #
    # 使用 Bayesian priorMean
    # 1~5 → 0~1
    # =========================================

    prior_mean = (
        breathing_effect.get(
            "priorMean"
        )
    )


    if isinstance(
        prior_mean,
        (int, float)
    ):

        prior_history = (
            float(prior_mean)
            - 1.0
        ) / 4.0


        return max(
            0.0,
            min(
                prior_history,
                1.0
            )
        )


    # =========================================
    # 3. 完全沒有歷史資料
    # =========================================

    return None

# =========================================================
# Breathing Recommendation Score
# =========================================================

def calculate_breathing_score(
    breathing: str,
    state_fit: float,
    goal_fit: float,
    baseline_fit: float,
    history_snapshot: dict | None,
) -> dict:
    """
    計算單一 Breathing 的推薦分數。

    完全沒有 History：
    0.40 State
    + 0.30 Goal
    + 0.30 Baseline

    有 History：
    0.40 State
    + 0.30 Goal
    + 0.10 Baseline
    + 0.20 History
    """

    history_fit = (
        get_breathing_history_score(
            breathing=breathing,
            history_snapshot=history_snapshot,
        )
    )


    # =========================================
    # Cold Start
    # =========================================

    if history_fit is None:

        score = (
            STATE_WEIGHT * state_fit
            +
            GOAL_WEIGHT * goal_fit
            +
            COLD_START_BASELINE_WEIGHT
            * baseline_fit
        )


        return {
            "score":
                round(score, 4),

            "stateFit":
                round(state_fit, 4),

            "goalFit":
                round(goal_fit, 4),

            "baselineFit":
                round(baseline_fit, 4),

            "historyFit":
                None,

            "mode":
                "cold_start",
        }


    # =========================================
    # History Mode
    # =========================================

    score = (
        STATE_WEIGHT * state_fit
        +
        GOAL_WEIGHT * goal_fit
        +
        HISTORY_BASELINE_WEIGHT
        * baseline_fit
        +
        HISTORY_WEIGHT
        * history_fit
    )


    return {
        "score":
            round(score, 4),

        "stateFit":
            round(state_fit, 4),

        "goalFit":
            round(goal_fit, 4),

        "baselineFit":
            round(baseline_fit, 4),

        "historyFit":
            round(history_fit, 4),

        "mode":
            "history",
    }

# =========================================================
# Breathing Ranking with History
# =========================================================

def rank_breathing_candidates(
    state: str,
    goal: str,
    baseline_ranking: list,
    state_matrix: dict,
    goal_matrix: dict,
    history_snapshot: dict | None,
) -> list:
    """
    Breathing 專用 Ranking。

    - 沒有 History → Cold Start
    - 有 History → 納入 Breathing History
    """

    # =========================================
    # 1. 檢查 State
    # =========================================

    if state not in state_matrix:
        raise ValueError(
            f"State Matrix 中不存在 state：{state}"
        )


    # =========================================
    # 2. 檢查 Goal
    # =========================================

    if goal not in goal_matrix:
        raise ValueError(
            f"Goal Matrix 中不存在 goal：{goal}"
        )


    # =========================================
    # 3. Baseline Ranking list → dict
    # =========================================

    baseline_scores = {
        item["id"]:
            item["baselineFit"]

        for item
        in baseline_ranking
    }


    results = []


    # =========================================
    # 4. 計算所有 Breathing
    # =========================================

    for breathing in state_matrix[state]:

        if breathing not in goal_matrix[goal]:
            raise ValueError(
                f"Goal Matrix 缺少 Breathing："
                f"{breathing}"
            )


        if breathing not in baseline_scores:
            raise ValueError(
                f"Baseline Ranking 缺少 Breathing："
                f"{breathing}"
            )


        state_fit = (
            state_matrix[
                state
            ][breathing]
        )


        goal_fit = (
            goal_matrix[
                goal
            ][breathing]
        )


        baseline_fit = (
            baseline_scores[
                breathing
            ]
        )


        score_result = (
            calculate_breathing_score(
                breathing=breathing,
                state_fit=state_fit,
                goal_fit=goal_fit,
                baseline_fit=baseline_fit,
                history_snapshot=
                    history_snapshot,
            )
        )


        results.append({
            "id":
                breathing,

            **score_result,
        })


    # =========================================
    # 5. 高分 → 低分
    # =========================================

    results.sort(
        key=lambda item:
            item["score"],
        reverse=True,
    )


    return results


# =========================================================
# Scene History 1~5 Score → 0~1
# =========================================================

def normalize_history_score(
    score: float | None
) -> float | None:

    if not isinstance(
        score,
        (int, float)
    ):
        return None

    normalized = (
        float(score) - 1.0
    ) / 4.0

    return max(
        0.0,
        min(
            normalized,
            1.0
        )
    )

# =========================================================
# Scene Preference Fit
# =========================================================

def get_scene_preference_fit(
    scene: str,
    history_snapshot: dict | None,
) -> float | None:

    if not isinstance(
        history_snapshot,
        dict
    ):
        return None


    scene_preference = (
        history_snapshot.get(
            "scenePreference"
        )
    )


    if not isinstance(
        scene_preference,
        dict
    ):
        return None


    items = (
        scene_preference.get(
            "items"
        )
    )


    if isinstance(
        items,
        dict
    ):

        item = items.get(
            scene
        )

        if isinstance(
            item,
            dict
        ):

            preference = (
                item.get(
                    "preference"
                )
            )

            if isinstance(
                preference,
                (int, float)
            ):

                return (
                    normalize_history_score(
                        preference
                    )
                )


    # =========================================
    # 沒有此場景個別資料
    # → Bayesian priorMean
    # =========================================

    prior_mean = (
        scene_preference.get(
            "priorMean"
        )
    )


    return normalize_history_score(
        prior_mean
    )

# =========================================================
# Scene Effect Fit
# =========================================================

def get_scene_effect_fit(
    scene: str,
    history_snapshot: dict | None,
) -> float | None:

    if not isinstance(
        history_snapshot,
        dict
    ):
        return None


    scene_effect = (
        history_snapshot.get(
            "sceneEffect"
        )
    )


    if not isinstance(
        scene_effect,
        dict
    ):
        return None


    items = (
        scene_effect.get(
            "items"
        )
    )


    if isinstance(
        items,
        dict
    ):

        item = items.get(
            scene
        )

        if isinstance(
            item,
            dict
        ):

            effect = (
                item.get(
                    "effect"
                )
            )

            if isinstance(
                effect,
                (int, float)
            ):

                return (
                    normalize_history_score(
                        effect
                    )
                )


    # =========================================
    # 沒有此場景個別效果
    # → Bayesian priorMean
    # =========================================

    prior_mean = (
        scene_effect.get(
            "priorMean"
        )
    )


    return normalize_history_score(
        prior_mean
    )

# =========================================================
# Scene Familiarity
# =========================================================

def get_scene_familiarity(
    scene: str,
    history_snapshot: dict | None,
) -> float | None:
    """
    Familiarity(s)
    =
    該場景最近 7 天使用次數
    /
    所有場景中的最高使用次數

    0 = 相對陌生
    1 = 相對熟悉
    """

    if not isinstance(
        history_snapshot,
        dict
    ):
        return None


    scene_effect = (
        history_snapshot.get(
            "sceneEffect"
        )
    )


    if not isinstance(
        scene_effect,
        dict
    ):
        return None


    items = (
        scene_effect.get(
            "items"
        )
    )


    if not isinstance(
        items,
        dict
    ):
        return None


    counts = {}


    for scene_id, item in items.items():

        if not isinstance(
            item,
            dict
        ):
            continue


        count = (
            item.get(
                "completionSampleCount",
                0
            )
        )


        if not isinstance(
            count,
            (int, float)
        ):
            count = 0


        counts[
            scene_id
        ] = float(count)


    if len(counts) == 0:
        return None


    max_count = max(
        counts.values()
    )


    # 完全沒有使用紀錄
    if max_count <= 0:
        return None


    scene_count = (
        counts.get(
            scene,
            0.0
        )
    )


    return min(
        scene_count / max_count,
        1.0
    )

# =========================================================
# Scene Explore Fit
# =========================================================

def get_scene_explore_fit(
    scene: str,
    history_snapshot: dict | None,
) -> float | None:

    if not isinstance(
        history_snapshot,
        dict
    ):
        return None


    explore_data = (
        history_snapshot.get(
            "exploreScore"
        )
    )


    if not isinstance(
        explore_data,
        dict
    ):
        return None


    explore_score = (
        explore_data.get(
            "score"
        )
    )


    if not isinstance(
        explore_score,
        (int, float)
    ):
        return None


    familiarity = (
        get_scene_familiarity(
            scene,
            history_snapshot,
        )
    )


    if familiarity is None:
        # 沒有足夠場景使用紀錄時，
        # Exploration 不偏向任何候選
        return 0.5


    explore_score = max(
        0.0,
        min(
            float(explore_score),
            1.0
        )
    )


    # =========================================
    # ExploreScore 高
    # → 偏好陌生場景
    #
    # ExploreScore 低
    # → 偏好熟悉場景
    # =========================================

    explore_fit = (
        explore_score
        * (1.0 - familiarity)
        +
        (1.0 - explore_score)
        * familiarity
    )


    return round(
        explore_fit,
        6
    )

# =========================================================
# Scene History Score
# =========================================================

def get_scene_history_score(
    scene: str,
    history_snapshot: dict | None,
) -> dict | None:

    preference_fit = (
        get_scene_preference_fit(
            scene,
            history_snapshot,
        )
    )


    effect_fit = (
        get_scene_effect_fit(
            scene,
            history_snapshot,
        )
    )


    explore_fit = (
        get_scene_explore_fit(
            scene,
            history_snapshot,
        )
    )


    # =========================================
    # 完全沒有 Scene History
    # → Cold Start
    # =========================================

    if (
        preference_fit is None
        and effect_fit is None
        and explore_fit is None
    ):
        return None


    # =========================================
    # 個別訊號沒有資料時
    # 使用 0.5 作為中性值
    # =========================================

    if preference_fit is None:
        preference_fit = 0.5

    if effect_fit is None:
        effect_fit = 0.5

    if explore_fit is None:
        explore_fit = 0.5


    familiarity = (
        get_scene_familiarity(
            scene,
            history_snapshot,
        )
    )


    history_fit = (
        0.45 * preference_fit
        +
        0.45 * effect_fit
        +
        0.10 * explore_fit
    )


    return {
        "historyFit":
            round(
                history_fit,
                4
            ),

        "preferenceFit":
            round(
                preference_fit,
                4
            ),

        "effectFit":
            round(
                effect_fit,
                4
            ),

        "exploreFit":
            round(
                explore_fit,
                4
            ),

        "familiarity":
            (
                None
                if familiarity is None
                else round(
                    familiarity,
                    4
                )
            ),
    }

# =========================================================
# Scene Recommendation Score
# =========================================================

def calculate_scene_score(
    scene: str,
    state_fit: float,
    goal_fit: float,
    baseline_fit: float,
    history_snapshot: dict | None,
) -> dict:

    history_result = (
        get_scene_history_score(
            scene,
            history_snapshot,
        )
    )


    # =========================================
    # Cold Start
    # =========================================

    if history_result is None:

        score = (
            STATE_WEIGHT * state_fit
            +
            GOAL_WEIGHT * goal_fit
            +
            COLD_START_BASELINE_WEIGHT
            * baseline_fit
        )


        return {
            "score":
                round(score, 4),

            "stateFit":
                round(state_fit, 4),

            "goalFit":
                round(goal_fit, 4),

            "baselineFit":
                round(baseline_fit, 4),

            "historyFit":
                None,

            "mode":
                "cold_start",
        }


    # =========================================
    # History Mode
    # =========================================

    history_fit = (
        history_result[
            "historyFit"
        ]
    )


    score = (
        STATE_WEIGHT * state_fit
        +
        GOAL_WEIGHT * goal_fit
        +
        HISTORY_BASELINE_WEIGHT
        * baseline_fit
        +
        HISTORY_WEIGHT
        * history_fit
    )


    return {
        "score":
            round(score, 4),

        "stateFit":
            round(state_fit, 4),

        "goalFit":
            round(goal_fit, 4),

        "baselineFit":
            round(baseline_fit, 4),

        **history_result,

        "mode":
            "history",
    }

# =========================================================
# Scene Ranking with History
# =========================================================

def rank_scene_candidates(
    state: str,
    goal: str,
    baseline_ranking: list,
    state_matrix: dict,
    goal_matrix: dict,
    history_snapshot: dict | None,
) -> list:

    if state not in state_matrix:
        raise ValueError(
            f"State Matrix 中不存在 state：{state}"
        )


    if goal not in goal_matrix:
        raise ValueError(
            f"Goal Matrix 中不存在 goal：{goal}"
        )


    baseline_scores = {
        item["id"]:
            item["baselineFit"]

        for item
        in baseline_ranking
    }


    results = []


    for scene in state_matrix[state]:

        if scene not in goal_matrix[goal]:
            raise ValueError(
                f"Goal Matrix 缺少 Scene：{scene}"
            )


        if scene not in baseline_scores:
            raise ValueError(
                f"Baseline Ranking 缺少 Scene：{scene}"
            )


        state_fit = (
            state_matrix[
                state
            ][scene]
        )


        goal_fit = (
            goal_matrix[
                goal
            ][scene]
        )


        baseline_fit = (
            baseline_scores[
                scene
            ]
        )


        score_result = (
            calculate_scene_score(
                scene=scene,
                state_fit=state_fit,
                goal_fit=goal_fit,
                baseline_fit=baseline_fit,
                history_snapshot=
                    history_snapshot,
            )
        )


        results.append({
            "id":
                scene,

            **score_result,
        })


    results.sort(
        key=lambda item:
            item["score"],
        reverse=True,
    )


    return results