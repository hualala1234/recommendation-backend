from recommendation.mappings import (
    GUIDANCE_MAPPING,
)
# ==========================================================
# Guidance Style -> Voice Parameters
#
# 這裡不是推薦分數，而是固定 Rule Mapping。
# Guidance 一旦決定，就直接推導 Voice Parameters。
# ==========================================================


GUIDANCE_VOICE_PARAMETERS = {

    # 溫柔陪伴
    "gentle_companion": {
        "voiceTone": "warm_gentle",
        "speed": "slow",
        "density": "medium",
        "silenceRatio": {
            "min": 0.30,
            "max": 0.35,
        },
    },

    # 清楚引導
    "structured_guidance": {
        "voiceTone": "calm_clear",
        "speed": "medium_slow",
        "density": "high",
        "silenceRatio": {
            "min": 0.15,
            "max": 0.20,
        },
    },

    # 環境聲 / 極少人聲
    "ambient_minimal": {
        "voiceTone": "soft",
        "speed": "slow",
        "density": "very_low",
        "silenceRatio": {
            "min": 0.70,
            "max": 0.80,
        },
    },

    # 少量鼓勵
    "sparse_encouragement": {
        "voiceTone": "warm_gentle",
        "speed": "slow",
        "density": "low",
        "silenceRatio": {
            "min": 0.55,
            "max": 0.65,
        },
    },
}


def get_guidance_voice_parameters(
    guidance: str
) -> dict:
    """
    根據 Guidance Style 取得固定的 Voice Parameters。
    """

    if guidance not in GUIDANCE_VOICE_PARAMETERS:
        raise ValueError(
            f"未知 Guidance Style：{guidance}"
        )

    # 回傳 copy，避免外部不小心修改原始設定
    params = GUIDANCE_VOICE_PARAMETERS[
        guidance
    ]

    return {
        "voiceTone": params["voiceTone"],
        "speed": params["speed"],
        "density": params["density"],
        "silenceRatio": {
            "min": params["silenceRatio"]["min"],
            "max": params["silenceRatio"]["max"],
        },
    }

# =========================================================
# Guidance History Fallback
# =========================================================

def get_guidance_history_fallback(
    history_snapshot: dict | None,
) -> dict | None:
    """
    當本次沒有 Pre Q2 明確 Guidance 時，
    從 guidanceEffect.items 中選擇
    GuideRank 最高的 Guidance。

    回傳 Recommendation 使用的 Guidance Style。
    """

    if not isinstance(
        history_snapshot,
        dict
    ):
        return None


    guidance_effect = (
        history_snapshot.get(
            "guidanceEffect"
        )
    )


    if not isinstance(
        guidance_effect,
        dict
    ):
        return None


    items = (
        guidance_effect.get(
            "items"
        )
    )


    if not isinstance(
        items,
        dict
    ):
        return None


    # =====================================================
    # 先確認真的有 Guidance History
    #
    # 可能來源：
    # 1. recentGuidance 有 Pre Q2 歷史
    # 2. guidanceEffect 有實際 Post Q1 效果
    # =====================================================

    recent_guidance = (
        history_snapshot.get(
            "recentGuidance"
        )
    )


    recent_sample_count = 0

    if isinstance(
        recent_guidance,
        dict
    ):
        value = (
            recent_guidance.get(
                "sampleCount",
                0
            )
        )

        if isinstance(
            value,
            (int, float)
        ):
            recent_sample_count = int(
                value
            )


    effect_sample_count = 0

    for item in items.values():

        if not isinstance(
            item,
            dict
        ):
            continue

        count = (
            item.get(
                "sampleCount",
                0
            )
        )

        if isinstance(
            count,
            (int, float)
        ):
            effect_sample_count += int(
                count
            )


    # 完全沒有 Guidance 歷史
    if (
        recent_sample_count <= 0
        and effect_sample_count <= 0
    ):
        return None


    # =====================================================
    # 找出有效 GuideRank
    # =====================================================

    candidates = []


    for history_key, item in items.items():

        if not isinstance(
            item,
            dict
        ):
            continue


        rank = item.get(
            "rank"
        )


        if not isinstance(
            rank,
            (int, float)
        ):
            continue


        guidance_style = (
            GUIDANCE_MAPPING.get(
                history_key
            )
        )


        if guidance_style is None:
            continue


        candidates.append({
            "id":
                guidance_style,

            "historyKey":
                history_key,

            "rank":
                float(rank),

            "preferenceNorm":
                item.get(
                    "preferenceNorm"
                ),

            "effectNorm":
                item.get(
                    "effectNorm"
                ),

            "sampleCount":
                item.get(
                    "sampleCount",
                    0
                ),
        })


    if len(candidates) == 0:
        return None


    # =====================================================
    # Rank 高 → 低
    #
    # 同分時：
    # PreferenceNorm 高者優先
    # 再同分則 EffectNorm 高者優先
    # =====================================================

    candidates.sort(
        key=lambda item: (
            item["rank"],

            (
                item["preferenceNorm"]
                if isinstance(
                    item["preferenceNorm"],
                    (int, float)
                )
                else -1
            ),

            (
                item["effectNorm"]
                if isinstance(
                    item["effectNorm"],
                    (int, float)
                )
                else -1
            ),
        ),
        reverse=True,
    )


    top = candidates[0]


    return {
        "id":
            top["id"],

        "historyKey":
            top["historyKey"],

        "rank":
            round(
                top["rank"],
                4
            ),

        "ranking":
            [
                {
                    **item,

                    "rank":
                        round(
                            item["rank"],
                            4
                        ),
                }

                for item
                in candidates
            ],
    }