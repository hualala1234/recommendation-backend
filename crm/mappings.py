# =========================================================
# CRM Display / Tag Mappings
#
# History / Recommendation 內部統一使用英文 key。
# 這個檔案只負責：
#
# 1. CRM 一般欄位顯示文字
# 2. CRM 標籤名稱
#
# 不在這裡重新計算 History 分數。
# =========================================================


# =========================================================
# 1. Recent State
#
# CRM 欄位：
# 近期主要狀態
# =========================================================

RECENT_STATE_CRM_VALUES = {
    "tense_anxious":
        "焦慮緊繃",

    "fatigued_low_energy":
        "疲勞",

    "racing_thoughts":
        "思緒繁多",

    "calm_relax":
        "平穩放鬆",
}


# =========================================================
# 2. Recent Goal
#
# CRM 欄位：
# 近期主要目標
# =========================================================

RECENT_GOAL_CRM_VALUES = {
    "relax":
        "放鬆",

    "focus":
        "專注",

    "mental_reset":
        "放空",

    "sleep":
        "睡眠",

    "self_compassion":
        "舒緩情緒",
}


# =========================================================
# 3. Recent Guidance Preference
#
# CRM 欄位：
# 近期引導偏好
# =========================================================

RECENT_GUIDANCE_CRM_VALUES = {
    "gentle_companion":
        "溫柔陪伴",

    "guided_relaxation":
        "引導式",

    "ambient_only":
        "環境聲",

    "quiet_with_encouragement":
        "少量鼓勵",
}


# =========================================================
# 4. Recent Effect
#
# CRM 一般欄位：
# 近期效果分數
#
# CRM 標籤：
# 近期效果/佳
# 近期效果/普通
# 近期效果/有限
#
# 對應 history/classifiers.py：
#
# good
# normal
# limited
# =========================================================

RECENT_EFFECT_TAGS = {
    "good":
        "近期效果/佳",

    "normal":
        "近期效果/普通",

    "limited":
        "近期效果/有限",
}


# =========================================================
# 5. Recent Intent
#
# CRM 一般欄位：
# 近期使用意願
#
# CRM 標籤：
# 使用意願/願意再次使用
# 使用意願/想探索其他
# 使用意願/暫時不想使用
# =========================================================

RECENT_INTENT_CRM_VALUES = {
    "reuse_same":
        "願意再次使用",

    "explore_other":
        "想探索其他",

    "sleep_signal":
        "暫時不想使用",
}


RECENT_INTENT_TAGS = {
    "reuse_same":
        "使用意願/願意再次使用",

    "explore_other":
        "使用意願/想探索其他",

    "sleep_signal":
        "使用意願/暫時不想使用",
}


# =========================================================
# 6. Scene Preference
#
# CRM 欄位：
# 偏好場景
#
# 由 scenePreference 中找出偏好最高的場景。
# =========================================================

SCENE_CRM_VALUES = {
    "forest":
        "森林",

    "ocean":
        "海邊",

    "mountain":
        "高山",

    "field":
        "小麥田",
}


# =========================================================
# 7. Preferred Duration
#
# CRM 一般欄位：
# 偏好時長
#
# CRM 實際儲存 minutes 數值。
#
# 此 Mapping 可用於需要顯示
# 「短時 / 適中 / 長時」時使用。
#
# 對應 history/classifiers.py：
#
# micro_session
# standard_short
# deep_immersion
# =========================================================

DURATION_CRM_VALUES = {
    "micro_session":
        "短時",

    "standard_short":
        "適中",

    "deep_immersion":
        "長時",
}


# =========================================================
# 8. Usage Frequency
#
# CRM 一般欄位：
# 近7日使用次數
#
# CRM 標籤：
# 使用頻率/近期休眠
# 使用頻率/偶發探索
# 使用頻率/習慣養成
# 使用頻率/高度沉浸
#
# 對應 classify_usage_frequency()
# =========================================================

USAGE_FREQUENCY_TAGS = {
    "dormant":
        "使用頻率/近期休眠",

    "occasional":
        "使用頻率/偶發探索",

    "habit_building":
        "使用頻率/習慣養成",

    "high_engagement":
        "使用頻率/高度沉浸",
}


# =========================================================
# 9. Completion
#
# CRM 一般欄位：
# 近期完成率
#
# CRM 標籤：
# 完成狀況/穩定完成
# 完成狀況/一般
# 完成狀況/常提早結束
#
# 對應 classify_completion()
# =========================================================

COMPLETION_TAGS = {
    "stable":
        "完成狀況/穩定完成",

    "normal":
        "完成狀況/一般",

    "often_ends_early":
        "完成狀況/常提早結束",
}


# =========================================================
# 10. Technique Effect Tags
#
# 對應 history/classifiers.py
# classify_effect_level()
#
# very_high
# high
# medium
# low
# very_low
#
# 這是 CRM 標籤，
# 和「高效果冥想技巧」複選一般欄位是兩件事。
# =========================================================

TECHNIQUE_EFFECT_TAGS = {
    "very_high":
        "高效果冥想技巧/極高效果冥想技巧",

    "high":
        "高效果冥想技巧/高效果冥想技巧",

    "medium":
        "高效果冥想技巧/中等效果冥想技巧",

    "low":
        "高效果冥想技巧/低效果冥想技巧",

    "very_low":
        "高效果冥想技巧/極低效果冥想技巧",
}


# =========================================================
# 11. High Effect Technique
#
# CRM 一般欄位：
# 高效果冥想技巧
#
# 欄位型態：
# 複選
#
# effect >= 3.41 才加入
# =========================================================

HIGH_EFFECT_TECHNIQUE_THRESHOLD = 3.41


TECHNIQUE_CRM_VALUES = {
    "breath_awareness":
        "呼吸覺察",

    "body_scan":
        "身體掃描",

    "grounding":
        "接地練習",

    "mindfulness":
        "正念",

    "visualization":
        "意象引導",

    "self_compassion":
        "自我關懷",
}


# =========================================================
# 12. Preferred Time
#
# CRM 欄位：
# 常用時段
#
# preferredTime.primary 可能有 1～2 個值。
# 如果 CRM 欄位支援複選，可以全部同步。
# =========================================================

PREFERRED_TIME_CRM_VALUES = {
    "morning":
        "早晨",

    "daytime":
        "下午",

    "evening":
        "晚上",

    "late_night":
        "深夜",
}