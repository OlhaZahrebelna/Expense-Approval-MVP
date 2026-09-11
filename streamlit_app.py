import os

import requests
import streamlit as st


# =========================================================
# Configuration
# =========================================================

API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8000",
)


st.set_page_config(
    page_title="Expense Approval MVP",
    page_icon="💰",
    layout="wide",
)


# =========================================================
# Session state
# =========================================================

if "token" not in st.session_state:
    st.session_state.token = None

if "user" not in st.session_state:
    st.session_state.user = None

if "page" not in st.session_state:
    st.session_state.page = "My expenses"

if "selected_expense_id" not in st.session_state:
    st.session_state.selected_expense_id = None


# =========================================================
# API helpers
# =========================================================

def auth_headers():
    return {
        "Authorization": f"Bearer {st.session_state.token}"
    }


def api_get(path):
    try:
        return requests.get(
            f"{API_URL}{path}",
            headers=auth_headers(),
            timeout=60,
        )

    except requests.RequestException:
        return None


def api_post(path, payload=None):
    try:
        return requests.post(
            f"{API_URL}{path}",
            headers=auth_headers(),
            json=payload,
            timeout=60,
        )

    except requests.RequestException:
        return None


def logout():
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.page = "My expenses"
    st.session_state.selected_expense_id = None
    st.rerun()


# =========================================================
# Login
# =========================================================

def show_login():
    st.title("💰 Expense Approval MVP")

    st.write(
        "Sign in to manage and approve expense requests."
    )

    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.subheader("Sign in")

        with st.form("login_form"):
            email = st.text_input(
                "Email",
                placeholder="employee@test.com",
            )

            password = st.text_input(
                "Password",
                type="password",
            )

            submitted = st.form_submit_button(
                "Sign in",
                use_container_width=True,
            )

        if submitted:
            try:
                response = requests.post(
                    f"{API_URL}/auth/login",
                    json={
                        "email": email,
                        "password": password,
                    },
                    timeout=60,
                )

            except requests.RequestException:
                st.error(
                    "Could not connect to FastAPI backend."
                )
                return

            if response.status_code != 200:
                st.error("Invalid email or password")
                return

            token = response.json()["access_token"]

            try:
                user_response = requests.get(
                    f"{API_URL}/auth/me",
                    headers={
                        "Authorization": f"Bearer {token}"
                    },
                    timeout=60,
                )

            except requests.RequestException:
                st.error(
                    "Could not load user profile."
                )
                return

            if user_response.status_code != 200:
                st.error(
                    "Could not load user profile."
                )
                return

            st.session_state.token = token
            st.session_state.user = (
                user_response.json()
            )

            st.session_state.page = "My expenses"

            st.rerun()


# =========================================================
# Sidebar
# =========================================================

def show_sidebar():
    user = st.session_state.user

    with st.sidebar:
        st.title("💰 Expense Approval")

        st.write(f"**{user['name']}**")
        st.caption(user["email"])

        roles = []

        if user["is_employee"]:
            roles.append("Employee")

        if user["is_approver"]:
            roles.append("Approver")

        st.caption(" / ".join(roles))

        st.divider()

        if user["is_employee"]:
            if st.button(
                "📋 My expenses",
                use_container_width=True,
            ):
                st.session_state.page = (
                    "My expenses"
                )

                st.session_state.selected_expense_id = (
                    None
                )

                st.rerun()

            if st.button(
                "➕ New expense",
                use_container_width=True,
            ):
                st.session_state.page = (
                    "New expense"
                )

                st.session_state.selected_expense_id = (
                    None
                )

                st.rerun()

        if user["is_approver"]:
            if st.button(
                "✅ Approval queue",
                use_container_width=True,
            ):
                st.session_state.page = (
                    "Approval queue"
                )

                st.session_state.selected_expense_id = (
                    None
                )

                st.rerun()

        st.divider()

        if st.button(
            "Logout",
            use_container_width=True,
        ):
            logout()


# =========================================================
# My expenses
# =========================================================

def show_my_expenses():
    st.title("My Expenses")

    st.caption(
        "View your submitted expense requests "
        "and their current status."
    )

    top_left, top_right = st.columns(
        [4, 1]
    )

    with top_right:
        if st.button(
            "➕ New expense",
            use_container_width=True,
        ):
            st.session_state.page = "New expense"
            st.rerun()

    response = api_get("/expenses/my")

    if response is None:
        st.error(
            "Could not connect to FastAPI backend."
        )
        return

    if response.status_code != 200:
        st.error("Could not load expenses.")
        return

    expenses = response.json()

    if not expenses:
        st.info(
            "You do not have any expenses yet."
        )
        return

    st.divider()

    header = st.columns(
        [1.2, 1.3, 2.8, 1.1, 1.2, 1]
    )

    header[0].markdown("**Date**")
    header[1].markdown("**Category**")
    header[2].markdown("**Description**")
    header[3].markdown("**Amount**")
    header[4].markdown("**Status**")
    header[5].markdown("**Action**")

    st.divider()

    for expense in expenses:
        row = st.columns(
            [1.2, 1.3, 2.8, 1.1, 1.2, 1]
        )

        row[0].write(
            expense["expense_date"]
        )

        row[1].write(
            f'#{expense["category_id"]}'
        )

        row[2].write(
            expense["description"]
        )

        row[3].write(
            f'${expense["amount"]}'
        )

        status = expense["status"]

        with row[4]:
            if status == "approved":
                st.success("Approved")

            elif status == "rejected":
                st.error("Rejected")

            elif status == "withdrawn":
                st.info("Withdrawn")

            else:
                st.warning("Pending")

        with row[5]:
            if st.button(
                "View",
                key=f"view_{expense['id']}",
                use_container_width=True,
            ):
                st.session_state.selected_expense_id = (
                    expense["id"]
                )

                st.session_state.page = (
                    "Expense details"
                )

                st.rerun()

        if expense["status"] == "pending":
            if st.button(
                "Withdraw",
                key=f"withdraw_{expense['id']}",
            ):
                withdraw_response = api_post(
                    f"/expenses/{expense['id']}/withdraw"
                )

                if withdraw_response is None:
                    st.error(
                        "Could not connect to backend."
                    )

                elif (
                    withdraw_response.status_code
                    == 200
                ):
                    st.success(
                        "Expense withdrawn."
                    )
                    st.rerun()

                else:
                    st.error(
                        withdraw_response.json().get(
                            "detail",
                            "Could not withdraw expense.",
                        )
                    )

        st.divider()


# =========================================================
# New expense
# =========================================================

def show_new_expense():
    st.title("Create a New Expense")

    st.caption(
        "Fill in the details and submit "
        "your expense request."
    )

    category_response = api_get(
        "/expenses/categories"
    )

    if category_response is None:
        st.error(
            "Could not connect to FastAPI backend."
        )
        return

    if category_response.status_code != 200:
        st.error(
            "Could not load expense categories."
        )
        return

    categories = category_response.json()

    if not categories:
        st.warning(
            "No categories are available."
        )
        return

    category_map = {
    category["name"]: category["id"]
    for category in categories
    }

    with st.form("new_expense_form"):
        col1, col2 = st.columns(2)

        with col1:
            amount = st.number_input(
                "Amount (USD)",
                min_value=0.01,
                step=1.00,
                format="%.2f",
            )

        with col2:
            category_name = st.selectbox(
                "Category",
                options=list(
                    category_map.keys()
                ),
            )

        description = st.text_area(
            "Description",
            placeholder=(
                "Describe the expense..."
            ),
        )

        col3, col4 = st.columns(2)

        with col3:
            expense_date = st.date_input(
                "Expense date"
            )

        with col4:
            payment_details = st.text_input(
                "Payment details",
                placeholder=(
                    "Bank transfer / account..."
                ),
            )

        submitted = st.form_submit_button(
            "Submit Expense",
            use_container_width=True,
        )

    if submitted:
        if not description.strip():
            st.error(
                "Description is required."
            )
            return

        if not payment_details.strip():
            st.error(
                "Payment details are required."
            )
            return

        payload = {
            "amount": amount,
            "category_id": (
                category_map[category_name]
            ),
            "description": (
                description.strip()
            ),
            "expense_date": (
                expense_date.isoformat()
            ),
            "payment_details": (
                payment_details.strip()
            ),
        }

        response = api_post(
            "/expenses",
            payload,
        )

        if response is None:
            st.error(
                "Could not connect to backend."
            )
            return

        if response.status_code == 201:
            st.success(
                "Expense created successfully."
            )

            st.session_state.page = (
                "My expenses"
            )

            st.rerun()

        else:
            st.error(
                response.json().get(
                    "detail",
                    "Could not create expense.",
                )
            )


# =========================================================
# Approval queue
# =========================================================

def show_approval_queue():
    st.title("Approval Queue")

    st.caption(
        "Review expense requests "
        "assigned to you."
    )

    response = api_get(
        "/expenses/queue"
    )

    if response is None:
        st.error(
            "Could not connect to FastAPI backend."
        )
        return

    if response.status_code != 200:
        st.error(
            "Could not load approval queue."
        )
        return

    expenses = response.json()

    if not expenses:
        st.info(
            "No pending expenses "
            "assigned to you."
        )
        return

    st.divider()

    header = st.columns(
        [1.2, 2.8, 1.2, 1.2]
    )

    header[0].markdown("**Date**")
    header[1].markdown("**Description**")
    header[2].markdown("**Amount**")
    header[3].markdown("**Action**")

    st.divider()

    for expense in expenses:
        row = st.columns(
            [1.2, 2.8, 1.2, 1.2]
        )

        row[0].write(
            expense["expense_date"]
        )

        row[1].write(
            expense["description"]
        )

        row[2].write(
            f'${expense["amount"]}'
        )

        with row[3]:
            if st.button(
                "Review",
                key=f"review_{expense['id']}",
                use_container_width=True,
            ):
                st.session_state.selected_expense_id = (
                    expense["id"]
                )

                st.session_state.page = (
                    "Expense details"
                )

                st.rerun()

        st.divider()


# =========================================================
# Expense details
# =========================================================

def show_expense_details():
    expense_id = (
        st.session_state.selected_expense_id
    )

    if expense_id is None:
        st.warning(
            "No expense selected."
        )
        return

    response = api_get(
        f"/expenses/{expense_id}"
    )

    if response is None:
        st.error(
            "Could not connect to backend."
        )
        return

    if response.status_code != 200:
        st.error(
            response.json().get(
                "detail",
                "Could not load expense.",
            )
        )
        return

    expense = response.json()

    if st.button("← Back"):
        if (
            expense["approver_id"]
            == st.session_state.user["id"]
            and st.session_state.user[
                "is_approver"
            ]
        ):
            st.session_state.page = (
                "Approval queue"
            )
        else:
            st.session_state.page = (
                "My expenses"
            )

        st.session_state.selected_expense_id = (
            None
        )

        st.rerun()

    st.title(
        f"Expense #{expense['id']}"
    )

    status = expense["status"]

    if status == "approved":
        st.success("Approved")

    elif status == "rejected":
        st.error("Rejected")

    elif status == "withdrawn":
        st.info("Withdrawn")

    else:
        st.warning("Pending")

    st.divider()

    left, right = st.columns(
        [1.2, 1]
    )

    # -----------------------------------------------------
    # Expense details
    # -----------------------------------------------------

    with left:
        st.subheader("Expense Details")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Amount",
                f'${expense["amount"]}',
            )

        with col2:
            st.write(
                "**Expense date**"
            )
            st.write(
                expense["expense_date"]
            )

        st.write(
            f'**Category ID:** '
            f'{expense["category_id"]}'
        )

        st.write(
            f'**Employee ID:** '
            f'{expense["employee_id"]}'
        )

        st.write("**Description**")
        st.write(
            expense["description"]
        )

        st.write("**Payment details**")
        st.write(
            expense["payment_details"]
        )

        if expense.get(
            "rejection_comment"
        ):
            st.error(
                "Rejection comment: "
                + expense[
                    "rejection_comment"
                ]
            )

    # -----------------------------------------------------
    # AI analysis
    # -----------------------------------------------------

    with right:
        if (
            expense["approver_id"]
            == st.session_state.user["id"]
        ):
            st.subheader("🤖 AI Review")

            ai_analysis = expense.get(
                "ai_analysis"
            )

            if ai_analysis:
                st.write("**Summary**")

                st.write(
                    ai_analysis["summary"]
                )

                st.divider()

                if ai_analysis["flagged"]:
                    st.warning(
                        "Potential inconsistency"
                    )

                    if ai_analysis.get(
                        "reason"
                    ):
                        st.write(
                            ai_analysis[
                                "reason"
                            ]
                        )

                else:
                    st.success(
                        "No obvious inconsistencies "
                        "detected."
                    )

            else:
                st.info(
                    "AI analysis is currently "
                    "unavailable."
                )


    # =====================================================
    # Approver actions
    # =====================================================

    if (
        st.session_state.user[
            "is_approver"
        ]
        and expense["approver_id"]
        == st.session_state.user["id"]
        and expense["status"]
        == "pending"
    ):
        st.divider()

        st.subheader(
            "Approve or Reject"
        )

        approve_col, reject_col = (
            st.columns(2)
        )

        with approve_col:
            st.write(
                "Approve this expense request."
            )

            if st.button(
                "Approve",
                type="primary",
                use_container_width=True,
            ):
                approve_response = api_post(
                    f"/expenses/{expense_id}/approve"
                )

                if approve_response is None:
                    st.error(
                        "Could not connect "
                        "to backend."
                    )

                elif (
                    approve_response.status_code
                    == 200
                ):
                    st.success(
                        "Expense approved."
                    )

                    st.session_state.page = (
                        "Approval queue"
                    )

                    st.session_state.selected_expense_id = (
                        None
                    )

                    st.rerun()

                else:
                    st.error(
                        approve_response.json().get(
                            "detail",
                            "Could not approve "
                            "expense.",
                        )
                    )

        with reject_col:
            rejection_comment = st.text_area(
                "Rejection comment",
                placeholder=(
                    "Explain why the expense "
                    "is rejected..."
                ),
            )

            if st.button(
                "Reject",
                use_container_width=True,
            ):
                if not rejection_comment.strip():
                    st.error(
                        "Rejection comment "
                        "is required."
                    )

                else:
                    reject_response = api_post(
                        f"/expenses/{expense_id}/reject",
                        {
                            "comment": (
                                rejection_comment.strip()
                            )
                        },
                    )

                    if reject_response is None:
                        st.error(
                            "Could not connect "
                            "to backend."
                        )

                    elif (
                        reject_response.status_code
                        == 200
                    ):
                        st.success(
                            "Expense rejected."
                        )

                        st.session_state.page = (
                            "Approval queue"
                        )

                        st.session_state.selected_expense_id = (
                            None
                        )

                        st.rerun()

                    else:
                        st.error(
                            reject_response.json().get(
                                "detail",
                                "Could not reject "
                                "expense.",
                            )
                        )


# =========================================================
# Main application
# =========================================================

if not st.session_state.token:
    show_login()

else:
    show_sidebar()

    page = st.session_state.page

    if page == "My expenses":
        show_my_expenses()

    elif page == "New expense":
        show_new_expense()

    elif page == "Approval queue":
        show_approval_queue()

    elif page == "Expense details":
        show_expense_details()