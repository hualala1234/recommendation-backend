import os
import secrets

from fastapi import (
    FastAPI,
    HTTPException,
    Header,
)

from dotenv import load_dotenv

load_dotenv()


from recommendation.engine import (
    get_baseline_recommendation
)

from recommendation.engine import (
    get_baseline_recommendation,
    get_current_recommendation,
)

from firebase.firestore_service import (
    get_recent_sessions,
    split_history_windows,
    get_history_snapshot,
    get_all_user_ids,
)

from history.snapshot import (
    build_history_snapshot,
)

from crm.crm_sync import (
    build_crm_sync_payload,
    sync_user_to_crm
)

from crm.vital_crm_service import (
    check_api_key,
    search_customer_by_firebase_uid,
    update_customer_extended_fields,
    sync_customer_labels,
)

from history.refresh_service import (
    refresh_user_history_and_crm,
    refresh_all_histories_and_crm,
)

app = FastAPI(
    title="Meditation Recommendation API",
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "message": "Recommendation API is running"
    }


@app.get(
    "/api/recommendation/baseline/{user_id}"
)
def get_baseline(user_id: str):

    try:

        result = get_baseline_recommendation(
            user_id
        )

        return result

    except LookupError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        print("Recommendation error:", e)

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get(
    "/api/recommendation/current/"
    "{user_id}/{session_id}"
)
def get_current(
    user_id: str,
    session_id: str
):

    try:

        return get_current_recommendation(
            user_id,
            session_id
        )

    except LookupError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        print(
            "Current recommendation error:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get("/api/history/debug/{user_id}")
def debug_history_sessions(user_id: str):

    sessions = get_recent_sessions(
        user_id,
        days=28
    )

    windows = split_history_windows(
        sessions
    )

    return {
        "userId": user_id,

        "recent7DaysCount":
            len(windows["sessions7d"]),

        "recent28DaysCount":
            len(windows["sessions28d"]),

        "sessions7d":
            windows["sessions7d"],

        "sessions28d":
            windows["sessions28d"]
    }

@app.get(
    "/api/history/{user_id}"
)
def get_history(
    user_id: str
):
    sessions = get_recent_sessions(
        user_id,
        days=28
    )

    snapshot = (
        build_history_snapshot(
            sessions
        )
    )

    return {
        "userId": user_id,
        "history": snapshot,
    }

@app.post(
    "/api/history/{user_id}/refresh"
)
def refresh_history(
    user_id: str
):
    """
    重新計算使用者 History，
    儲存至 Firestore，
    並同步摘要資料至 Vital CRM。
    """

    return (
        refresh_user_history_and_crm(
            user_id
        )
    )

@app.get(
    "/api/history/{user_id}/saved"
)
def get_saved_history(
    user_id: str
):

    snapshot = (
        get_history_snapshot(
            user_id
        )
    )


    if snapshot is None:

        return {
            "userId": user_id,
            "hasHistory": False,
            "history": None,
        }


    return {
        "userId": user_id,
        "hasHistory": True,
        "history": snapshot,
    }

# =========================================================
# CRM Preview
#
# 只測試：
# Firestore History
# -> CRM Fields / Labels
#
# 不會真的寫入 Vital CRM
# =========================================================

@app.get(
    "/api/crm/preview/{user_id}"
)
def preview_crm_sync(
    user_id: str
):

    history = (
        get_history_snapshot(
            user_id
        )
    )

    if history is None:
        raise HTTPException(
            status_code=404,
            detail="找不到 History Snapshot"
        )


    crm_payload = (
        build_crm_sync_payload(
            user_id=user_id,
            history=history,
        )
    )


    return {
        "userId":
            user_id,

        "crmPayload":
            crm_payload,
    }

# =========================================================
# Vital CRM Connection Test
# =========================================================

@app.get(
    "/api/crm/test-connection"
)
def test_crm_connection():

    return check_api_key()

# =========================================================
# Search CRM Customer By FirebaseUid
# =========================================================

@app.get(
    "/api/crm/customer/{user_id}"
)
def get_crm_customer(
    user_id: str
):

    return (
        search_customer_by_firebase_uid(
            user_id
        )
    )

@app.post(
    "/api/crm/test-sync-fields/{user_id}"
)
def test_sync_crm_fields(
    user_id: str,
):

    # 1. 取得 History
    history = (
        get_history_snapshot(
            user_id
        )
    )

    if history is None:
        raise HTTPException(
            status_code=404,
            detail="找不到 History Snapshot"
        )


    # 2. 建立 CRM Payload
    crm_payload = (
        build_crm_sync_payload(
            user_id=user_id,
            history=history,
        )
    )


    # 3. 找 CRM Customer
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

            "result":
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
                "找不到 CRM 客戶",
        }


    customers = (
        customer_result.get(
            "customers",
            []
        )
    )


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


    # 4. 更新 CRM 一般欄位
    update_result = (
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


    return {
        "userId":
            user_id,

        "customerId":
            customer_id,

        "customerNo":
            customer_no,

        "updateResult":
            update_result,
    }

@app.post(
    "/api/crm/test-sync-labels/{user_id}"
)
def test_sync_crm_labels(
    user_id: str,
):

    # 1. History
    history = (
        get_history_snapshot(
            user_id
        )
    )

    if history is None:

        raise HTTPException(
            status_code=404,
            detail="找不到 History Snapshot",
        )


    # 2. CRM Payload
    crm_payload = (
        build_crm_sync_payload(
            user_id=user_id,
            history=history,
        )
    )


    # 3. 找 CRM Customer
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

            "result":
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
                "找不到 CRM 客戶",
        }


    customers = (
        customer_result.get(
            "customers",
            []
        )
    )


    if len(customers) != 1:

        return {
            "success": False,

            "message":
                "FirebaseUid 對應的 CRM 客戶數量不是 1",

            "count":
                len(customers),
        }


    customer = customers[0]

    customer_no = (
        customer.get(
            "CustomerNo"
        )
    )


    # 4. 同步 CRM Labels
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


    return {
        "userId":
            user_id,

        "customerNo":
            customer_no,

        "sourceLabels":
            crm_payload[
                "labels"
            ],

        "labelResult":
            label_result,
    }

@app.post(
    "/api/crm/sync/{user_id}"
)
def sync_crm(
    user_id: str,
):

    history = (
        get_history_snapshot(
            user_id
        )
    )


    if history is None:

        raise HTTPException(
            status_code=404,
            detail="找不到 History Snapshot",
        )


    result = (
        sync_user_to_crm(
            user_id=user_id,
            history=history,
        )
    )


    return {
        "userId":
            user_id,

        "crmSync":
            result,
    }

@app.get(
    "/api/history-users"
)
def get_history_users():

    user_ids = (
        get_all_user_ids()
    )

    return {
        "count": len(user_ids),
        "userIds": user_ids,
    }

@app.post(
    "/api/history/refresh-all"
)
def refresh_all_history(
    x_cron_secret: str | None = Header(
        default=None
    )
):

    expected_secret = os.getenv(
        "HISTORY_CRON_SECRET"
    )


    if (
        not expected_secret
        or
        not x_cron_secret
        or
        not secrets.compare_digest(
            x_cron_secret,
            expected_secret,
        )
    ):

        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
        )


    return (
        refresh_all_histories_and_crm()
    )