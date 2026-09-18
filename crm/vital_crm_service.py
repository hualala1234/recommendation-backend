import os

import requests
from dotenv import load_dotenv


# =========================================================
# Load Environment Variables
# =========================================================

load_dotenv()


VITAL_CRM_STORE_NAME = os.getenv(
    "VITAL_CRM_STORE_NAME"
)

VITAL_CRM_API_KEY = os.getenv(
    "VITAL_CRM_API_KEY"
)


# =========================================================
# Config Validation
# =========================================================

def _validate_config():

    if not VITAL_CRM_STORE_NAME:
        raise ValueError(
            "缺少環境變數 VITAL_CRM_STORE_NAME"
        )

    if not VITAL_CRM_API_KEY:
        raise ValueError(
            "缺少環境變數 VITAL_CRM_API_KEY"
        )


# =========================================================
# Base URL
# =========================================================

def _get_base_url() -> str:

    _validate_config()

    return (
        "https://crm-storeapi.vitalyun.com/"
        f"{VITAL_CRM_STORE_NAME}/api"
    )


# =========================================================
# Headers
# =========================================================

def _get_headers() -> dict:

    _validate_config()

    return {
        "Content-Type":
            "application/json",

        "Authorization":
            f"ApiKey {VITAL_CRM_API_KEY}",
    }


# =========================================================
# Check API Key
# =========================================================

def check_api_key() -> dict:

    url = (
        f"{_get_base_url()}/apikey"
    )

    try:

        response = requests.get(
            url,
            headers=_get_headers(),
            timeout=15,
        )

    except requests.RequestException as e:

        return {
            "success": False,
            "statusCode": None,
            "message":
                f"無法連線 Vital CRM：{str(e)}",
        }


    # API Key 正常
    if response.status_code == 200:

        return {
            "success": True,
            "statusCode":
                response.status_code,

            "message":
                "Vital CRM API Key 驗證成功",
        }


    # API Key / StoreName / request 有問題
    try:
        response_body = (
            response.json()
        )

    except ValueError:
        response_body = (
            response.text
        )


    return {
        "success": False,
        "statusCode":
            response.status_code,

        "message":
            "Vital CRM API Key 驗證失敗",

        "response":
            response_body,
    }


# =========================================================
# Search Customer By FirebaseUid
# =========================================================

def search_customer_by_firebase_uid(
    firebase_uid: str,
) -> dict:

    if not firebase_uid:
        raise ValueError(
            "firebase_uid 不可為空"
        )

    url = (
        f"{_get_base_url()}/customers/search/"
    )

    body = {
        "ExtendedField": {
            "FirebaseUid":
                firebase_uid,
        },
        "Page": 1,
        "PageSize": 10,
    }

    try:

        response = requests.post(
            url,
            headers=_get_headers(),
            json=body,
            timeout=15,
        )

    except requests.RequestException as e:

        return {
            "success": False,
            "statusCode": None,
            "message":
                f"無法連線 Vital CRM：{str(e)}",
        }


    # ---------------------------------------------
    # Request 失敗
    # ---------------------------------------------

    if response.status_code != 200:

        try:
            response_body = (
                response.json()
            )

        except ValueError:
            response_body = (
                response.text
            )

        return {
            "success": False,
            "statusCode":
                response.status_code,

            "message":
                "搜尋 CRM 客戶失敗",

            "response":
                response_body,
        }


    # ---------------------------------------------
    # Parse JSON
    # ---------------------------------------------

    try:

        result = response.json()

    except ValueError:

        return {
            "success": False,
            "statusCode":
                response.status_code,

            "message":
                "CRM 回傳內容不是合法 JSON",

            "response":
                response.text,
        }


    customers = result.get(
        "data",
        []
    )


    if not isinstance(
        customers,
        list,
    ):
        customers = []


    # ---------------------------------------------
    # 沒找到
    # ---------------------------------------------

    if len(customers) == 0:

        return {
            "success": True,
            "found": False,
            "statusCode": 200,

            "message":
                "找不到 FirebaseUid 對應的 CRM 客戶",

            "firebaseUid":
                firebase_uid,

            "customers": [],
        }


    # ---------------------------------------------
    # 找到
    # ---------------------------------------------

    return {
        "success": True,
        "found": True,
        "statusCode": 200,

        "firebaseUid":
            firebase_uid,

        "count":
            len(customers),

        "customers":
            customers,
    }

# =========================================================
# Update Customer Extended Fields
# =========================================================

def update_customer_extended_fields(
    customer_id: str,
    customer_no: str,
    extended_fields: dict,
) -> dict:

    if not customer_id:
        raise ValueError(
            "customer_id 不可為空"
        )

    if not isinstance(
        extended_fields,
        dict,
    ):
        raise ValueError(
            "extended_fields 必須是 dict"
        )


    url = (
        f"{_get_base_url()}"
        "/customers/extendedattrs/"
    )


    # Vital CRM 擴充欄位 API
    # 一般欄位內容以字串傳入
    crm_fields = {}

    for key, value in extended_fields.items():

        if value is None:
            continue

        if isinstance(value, bool):

            crm_fields[key] = (
                "Y"
                if value
                else "N"
            )

        elif isinstance(
            value,
            (int, float),
        ):

            crm_fields[key] = str(
                value
            )

        else:

            crm_fields[key] = str(
                value
            )


    body = [
        {
            "Id":
                customer_id,

            "No":
                customer_no,

            "ExtendedAttrs":
                crm_fields,
        }
    ]


    try:

        response = requests.put(
            url,
            headers=_get_headers(),
            json=body,
            timeout=15,
        )

    except requests.RequestException as e:

        return {
            "success": False,
            "statusCode": None,
            "message":
                f"無法連線 Vital CRM：{str(e)}",
        }


    try:

        response_body = (
            response.json()
        )

    except ValueError:

        response_body = (
            response.text
        )


    # MaintainExtendedAttrs
    # 成功通常是 202 Accepted
    if response.status_code == 202:

        return {
            "success": True,
            "statusCode":
                response.status_code,

            "message":
                "CRM 擴充欄位更新已接受",

            "response":
                response_body,

            "sentFields":
                crm_fields,
        }


    return {
        "success": False,
        "statusCode":
            response.status_code,

        "message":
            "CRM 擴充欄位更新失敗",

        "response":
            response_body,

        "sentFields":
            crm_fields,
    }

# =========================================================
# Replace Labels Under One Parent
#
# 例如：
#
# ParentLabelName = "近期效果"
# Labels = ["普通"]
#
# CRM 最終：
# 近期效果/普通
#
# 原本同階層的標籤會被替換。
# =========================================================

def replace_customer_label_group(
    customer_no: str,
    parent_label_name: str,
    labels: list[str],
) -> dict:

    if not customer_no:
        raise ValueError(
            "customer_no 不可為空"
        )

    if not parent_label_name:
        raise ValueError(
            "parent_label_name 不可為空"
        )

    if not isinstance(
        labels,
        list,
    ):
        raise ValueError(
            "labels 必須是 list"
        )


    url = (
        f"{_get_base_url()}"
        f"/customers/{customer_no}/labelrels"
    )


    body = {
        "ParentLabelName":
            parent_label_name,

        # CRM 標籤已經事先建立，
        # 避免因 typo 自動建立錯誤標籤。
        "CreateLabelIfNotExist":
            False,

        "Labels":
            labels,
    }


    try:

        response = requests.put(
            url,
            headers=_get_headers(),
            json=body,
            timeout=15,
        )

    except requests.RequestException as e:

        return {
            "success": False,
            "statusCode": None,
            "message":
                f"無法連線 Vital CRM：{str(e)}",
        }


    try:

        response_body = (
            response.json()
        )

    except ValueError:

        response_body = (
            response.text
        )


    if response.status_code == 200:

        return {
            "success": True,

            "statusCode":
                response.status_code,

            "parent":
                parent_label_name,

            "labels":
                labels,

            "response":
                response_body,
        }


    return {
        "success": False,

        "statusCode":
            response.status_code,

        "parent":
            parent_label_name,

        "labels":
            labels,

        "response":
            response_body,
    }

# =========================================================
# CRM Label Groups
# =========================================================

CRM_LABEL_PARENTS = [
    "近期效果",
    "使用意願",
    "使用頻率",
    "完成狀況",
    "高效果冥想技巧",
]


# =========================================================
# Sync Customer Labels
#
# crm_labels 格式：
#
# [
#   "近期效果/普通",
#   "使用意願/願意再次使用",
#   ...
# ]
#
# 送 CRM 時會轉成：
#
# ParentLabelName = "近期效果"
# Labels = ["普通"]
# =========================================================

def sync_customer_labels(
    customer_no: str,
    crm_labels: list[str],
) -> dict:

    grouped_labels = {
        parent: []
        for parent
        in CRM_LABEL_PARENTS
    }


    # ---------------------------------------------
    # 將完整 path 拆成 Parent / Child
    # ---------------------------------------------

    for full_label in crm_labels:

        if not isinstance(
            full_label,
            str,
        ):
            continue

        if "/" not in full_label:
            continue


        parent, child = (
            full_label.split(
                "/",
                1,
            )
        )


        if (
            parent
            not in grouped_labels
        ):
            continue


        grouped_labels[
            parent
        ].append(
            child
        )


    # ---------------------------------------------
    # 每個父階層分別 PUT
    # ---------------------------------------------

    results = {}


    for (
        parent,
        child_labels,
    ) in grouped_labels.items():

        result = (
            replace_customer_label_group(
                customer_no=
                    customer_no,

                parent_label_name=
                    parent,

                labels=
                    child_labels,
            )
        )


        results[
            parent
        ] = result


    success = all(
        result.get(
            "success",
            False,
        )
        for result
        in results.values()
    )


    return {
        "success":
            success,

        "groups":
            results,
    }

def batch_update_customer_extended_fields(
    customers: list[dict],
) -> dict:

    if not isinstance(customers, list):
        raise ValueError(
            "customers 必須是 list"
        )

    if len(customers) == 0:
        return {
            "success": True,
            "statusCode": None,
            "message": "沒有需要更新的 CRM 客戶",
        }

    if len(customers) > 50:
        raise ValueError(
            "Vital CRM 單次最多更新 50 位客戶"
        )


    url = (
        f"{_get_base_url()}"
        "/customers/extendedattrs/"
    )


    body = []


    for customer in customers:

        customer_id = customer.get(
            "customerId"
        )

        customer_no = customer.get(
            "customerNo"
        )

        extended_fields = customer.get(
            "extendedFields",
            {}
        )


        crm_fields = {}


        for key, value in extended_fields.items():

            if value is None:
                continue

            if isinstance(value, bool):

                crm_fields[key] = (
                    "Y"
                    if value
                    else "N"
                )

            else:

                crm_fields[key] = str(
                    value
                )


        body.append({
            "Id":
                customer_id,

            "No":
                customer_no,

            "ExtendedAttrs":
                crm_fields,
        })


    try:

        response = requests.put(
            url,
            headers=_get_headers(),
            json=body,
            timeout=30,
        )

    except requests.RequestException as e:

        return {
            "success": False,
            "statusCode": None,
            "message":
                f"無法連線 Vital CRM：{str(e)}",
        }


    try:

        response_body = (
            response.json()
        )

    except ValueError:

        response_body = (
            response.text
        )


    return {
        "success":
            response.status_code == 202,

        "statusCode":
            response.status_code,

        "count":
            len(body),

        "response":
            response_body,
    }