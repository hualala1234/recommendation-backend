from firebase.firestore_service import (
    get_recent_sessions,
    save_history_snapshot,
    get_all_user_ids,
)

from history.snapshot import (
    build_history_snapshot,
)

from crm.crm_sync import (
    build_crm_sync_payload,
    sync_user_to_crm,
)

from crm.vital_crm_service import (
    search_customer_by_firebase_uid,
    batch_update_customer_extended_fields,
    sync_customer_labels,
)


# =========================================================
# Rebuild One User History
# =========================================================

def rebuild_user_history(
    user_id: str,
):
    """
    重新計算單一使用者 History，
    並寫回 Firestore。

    不處理 CRM。
    """

    sessions = get_recent_sessions(
        user_id,
        days=28,
    )

    snapshot = (
        build_history_snapshot(
            sessions
        )
    )

    save_history_snapshot(
        user_id=user_id,
        history_snapshot=snapshot,
    )

    return sessions, snapshot


# =========================================================
# Refresh One User
#
# Unity 冥想完成後使用
# =========================================================

def refresh_user_history_and_crm(
    user_id: str,
) -> dict:
    """
    重新計算單一使用者 History，
    儲存至 Firestore，
    並同步至 Vital CRM。
    """

    # =========================================
    # 1. History
    # =========================================

    sessions, snapshot = (
        rebuild_user_history(
            user_id
        )
    )


    # =========================================
    # 2. CRM
    #
    # CRM 失敗不影響 History
    # =========================================

    try:

        crm_sync_result = (
            sync_user_to_crm(
                user_id=user_id,
                history=snapshot,
                sessions=sessions,
            )
        )


        if not crm_sync_result.get(
            "success",
            False,
        ):

            print(
                "[CRM Sync Warning]",
                user_id,
                crm_sync_result,
            )


    except Exception as e:

        print(
            "[CRM Sync Error]",
            user_id,
            str(e),
        )

        crm_sync_result = {
            "success": False,
            "message": str(e),
        }


    # =========================================
    # 3. Response
    # =========================================

    return {
        "success": True,
        "userId": user_id,
        "history": snapshot,
        "crmSync": crm_sync_result,
    }


# =========================================================
# Batch Helper
# =========================================================

def _chunk_list(
    items: list,
    size: int,
):

    for i in range(
        0,
        len(items),
        size,
    ):

        yield items[
            i:i + size
        ]


# =========================================================
# Refresh All Users
#
# 每日排程使用
# =========================================================

def refresh_all_histories_and_crm() -> dict:

    user_ids = (
        get_all_user_ids()
    )

    history_results = []

    crm_customers = []


    # =========================================
    # 1. 所有人重新計算 History
    # =========================================

    for user_id in user_ids:

        try:

            sessions, snapshot = (
                rebuild_user_history(
                    user_id
                )
            )


            # ---------------------------------
            # CRM Payload
            # ---------------------------------

            crm_payload = (
                build_crm_sync_payload(
                    user_id=user_id,
                    history=snapshot,
                    sessions=sessions,
                )
            )


            # ---------------------------------
            # 找 CRM Customer
            # ---------------------------------

            customer_result = (
                search_customer_by_firebase_uid(
                    user_id
                )
            )


            if not customer_result.get(
                "success",
                False,
            ):

                history_results.append({
                    "userId":
                        user_id,

                    "historySuccess":
                        True,

                    "crmPrepared":
                        False,

                    "message":
                        "搜尋 CRM 客戶失敗",
                })

                continue


            if not customer_result.get(
                "found",
                False,
            ):

                history_results.append({
                    "userId":
                        user_id,

                    "historySuccess":
                        True,

                    "crmPrepared":
                        False,

                    "message":
                        "找不到 CRM 客戶",
                })

                continue


            customers = (
                customer_result.get(
                    "customers",
                    []
                )
            )


            if len(customers) != 1:

                history_results.append({
                    "userId":
                        user_id,

                    "historySuccess":
                        True,

                    "crmPrepared":
                        False,

                    "message":
                        "CRM 客戶數量不是 1",

                    "crmCustomerCount":
                        len(customers),
                })

                continue


            customer = (
                customers[0]
            )


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


            if (
                not customer_id
                or
                not customer_no
            ):

                history_results.append({
                    "userId":
                        user_id,

                    "historySuccess":
                        True,

                    "crmPrepared":
                        False,

                    "message":
                        "CRM CustomerId 或 CustomerNo 不存在",
                })

                continue


            # ---------------------------------
            # 準備批次 CRM 資料
            # ---------------------------------

            crm_customers.append({
                "userId":
                    user_id,

                "customerId":
                    customer_id,

                "customerNo":
                    customer_no,

                "extendedFields":
                    crm_payload[
                        "extendedFields"
                    ],

                "labels":
                    crm_payload[
                        "labels"
                    ],
            })


            history_results.append({
                "userId":
                    user_id,

                "historySuccess":
                    True,

                "crmPrepared":
                    True,
            })


        except Exception as e:

            print(
                "[Daily Refresh Error]",
                user_id,
                str(e),
            )

            history_results.append({
                "userId":
                    user_id,

                "historySuccess":
                    False,

                "crmPrepared":
                    False,

                "message":
                    str(e),
            })


    # =========================================
    # 2. CRM 一般欄位
    #
    # Vital CRM 每批最多 50 人
    # =========================================

    field_results = []


    field_batch_data = [
        {
            "customerId":
                item["customerId"],

            "customerNo":
                item["customerNo"],

            "extendedFields":
                item["extendedFields"],
        }

        for item
        in crm_customers
    ]


    for batch in _chunk_list(
        field_batch_data,
        50,
    ):

        try:

            result = (
                batch_update_customer_extended_fields(
                    batch
                )
            )

            field_results.append(
                result
            )


        except Exception as e:

            field_results.append({
                "success": False,
                "message": str(e),
            })


    # =========================================
    # 3. CRM Labels
    # =========================================

    label_results = []


    for item in crm_customers:

        try:

            result = (
                sync_customer_labels(
                    customer_no=
                        item["customerNo"],

                    crm_labels=
                        item["labels"],
                )
            )


            label_results.append({
                "userId":
                    item["userId"],

                "success":
                    result.get(
                        "success",
                        False,
                    ),

                "result":
                    result,
            })


        except Exception as e:

            print(
                "[Daily CRM Label Error]",
                item["userId"],
                str(e),
            )

            label_results.append({
                "userId":
                    item["userId"],

                "success":
                    False,

                "message":
                    str(e),
            })


    # =========================================
    # 4. 統計結果
    # =========================================

    history_success = all(
        item.get(
            "historySuccess",
            False,
        )
        for item
        in history_results
    )


    fields_success = all(
        item.get(
            "success",
            False,
        )
        for item
        in field_results
    )


    labels_success = all(
        item.get(
            "success",
            False,
        )
        for item
        in label_results
    )


    crm_success = (
        fields_success
        and
        labels_success
    )


    # =========================================
    # 5. Response
    # =========================================

    return {
        "success":
            history_success,

        "historySuccess":
            history_success,

        "crmSuccess":
            crm_success,

        "totalUsers":
            len(user_ids),

        "crmCustomerCount":
            len(crm_customers),

        "historyResults":
            history_results,

        "crmFields":
            field_results,

        "crmLabels":
            label_results,
    }