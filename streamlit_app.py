import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="Expense Approval MVP",
    page_icon="💰",
    layout="wide",
)


if "token" not in st.session_state:
    st.session_state.token = None

if "user" not in st.session_state:
    st.session_state.user = None


st.title("Expense Approval MVP")


if not st.session_state.token:
    st.subheader("Sign in to your account")

    email = st.text_input("Email")

    password = st.text_input(
        "Password",
        type="password",
    )

    if st.button(
        "Sign in",
        use_container_width=True,
    ):
        response = requests.post(
            f"{API_URL}/auth/login",
            json={
                "email": email,
                "password": password,
            },
            timeout=10,
        )

        if response.status_code == 200:
            token = response.json()["access_token"]

            st.session_state.token = token

            user_response = requests.get(
                f"{API_URL}/auth/me",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                timeout=10,
            )

            if user_response.status_code == 200:
                st.session_state.user = user_response.json()
                st.rerun()

            else:
                st.error("Could not load user profile")

        else:
            st.error("Invalid email or password")

else:
    st.success(
        f"Logged in as {st.session_state.user['name']}"
    )

    st.write(st.session_state.user)

    if st.button("Logout"):
        st.session_state.token = None
        st.session_state.user = None
        st.rerun()


