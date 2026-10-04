import resend
import streamlit as st
from google import genai
from google.genai import types

from prompts import (
    SYSTEM_PROMPT,
    WELCOME_MESSAGE_TEMPLATE,
    SUMMARY_REQUEST_PROMPT,
)


# =========================================================
# CONFIGURATION
# =========================================================

MODEL_NAME = "gemini-3.5-flash-lite"

st.set_page_config(
    page_title="PackWise AI",
    page_icon="🧳",
    layout="wide",
    initial_sidebar_state="expanded",
)

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
RESEND_API_KEY = st.secrets["RESEND_API_KEY"]


# =========================================================
# GEMINI CLIENT
# =========================================================

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


gemini_client = get_gemini_client()


# =========================================================
# EMAIL
# =========================================================

def send_email(to_address, subject, body):

    resend.api_key = RESEND_API_KEY

    html_body = body.replace("\n", "<br>")

    params = {
        "from": "PackWise AI <onboarding@resend.dev>",
        "to": [to_address],
        "subject": subject,
        "html": f"""
        <html>
        <body style="
            font-family: Arial, sans-serif;
            line-height: 1.6;
            padding: 20px;
        ">

            <h2>🧳 Your PackWise AI Travel Plan</h2>

            <p>Hello!</p>

            <p>
                Here is your personalized travel packing plan:
            </p>

            <div>
                {html_body}
            </div>

            <br>

            <p>
                ✈️ <strong>
                Pack less. Travel smarter. Explore better.
                </strong>
            </p>

            <p>— PackWise AI</p>

        </body>
        </html>
        """,
    }

    return resend.Emails.send(params)


# =========================================================
# SESSION STATE
# =========================================================

def initialize_session():

    defaults = {
        "onboarded": False,
        "messages": [],
        "checklist": [],
        "name": "",
        "email": "",
        "destination": "",
        "trip_duration": 3,
        "trip_type": "Vacation",
        "luggage": "Backpack",
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


initialize_session()


# =========================================================
# GEMINI CHAT
# =========================================================

def create_chat():

    return gemini_client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT
        ),
    )


def ask_gemini(parts):

    try:

        response = st.session_state.chat.send_message(parts)

        return response.text

    except Exception as error:

        return f"Sorry, something went wrong: {error}"


# =========================================================
# MESSAGE FUNCTIONS
# =========================================================

def render_message(message):

    with st.chat_message(message["role"]):

        if message["kind"] == "text":

            st.write(message["content"])

        elif message["kind"] == "image":

            st.image(
                message["content"],
                caption="Uploaded travel items",
                use_container_width=True,
            )


def add_message(role, kind, content):

    message = {
        "role": role,
        "kind": kind,
        "content": content,
    }

    st.session_state.messages.append(message)

    render_message(message)


# =========================================================
# CHECKLIST GENERATION
# =========================================================

def generate_checklist():

    prompt = f"""
Create a practical and personalized travel packing
checklist for this traveler.

Traveler name:
{st.session_state.name}

Destination:
{st.session_state.destination}

Trip duration:
{st.session_state.trip_duration} days

Trip type:
{st.session_state.trip_type}

Luggage:
{st.session_state.luggage}

Return ONLY packing items.

Rules:
- One item per line.
- Do not number the items.
- Do not use categories.
- Do not use checkboxes.
- Keep the list practical.
- Consider the destination.
- Consider the trip duration.
- Consider the trip type.
- Consider the luggage limitation.
- Include important travel essentials.
- Avoid unnecessary duplicates.

Example:

Passport
Phone charger
3 T-shirts
2 Pants
Comfortable shoes
Toothbrush
Sunscreen
Travel adapter
"""

    try:

        response = gemini_client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )

        items = []

        for line in response.text.splitlines():

            item = line.strip()

            if not item:
                continue

            item = item.lstrip(
                "-•*0123456789. "
            )

            if item:
                items.append(item)

        return items

    except Exception as error:

        st.error(
            f"Unable to create checklist: {error}"
        )

        return []


# =========================================================
# NEW TRIP
# =========================================================

def start_new_trip():

    st.session_state.onboarded = False

    st.session_state.messages = []

    st.session_state.checklist = []

    st.session_state.name = ""

    st.session_state.email = ""

    st.session_state.destination = ""

    st.session_state.trip_duration = 3

    st.session_state.trip_type = "Vacation"

    st.session_state.luggage = "Backpack"

    if "chat" in st.session_state:

        del st.session_state["chat"]

    st.rerun()


# =========================================================
# ONBOARDING
# =========================================================

if not st.session_state.onboarded:

    st.title("🧳 PackWise AI")

    st.subheader(
        "Pack less. Travel smarter. Explore better. 🌎"
    )

    st.write(
        "Your AI-powered travel packing assistant."
    )

    st.divider()

    st.header("✈️ Let's plan your trip")

    st.write(
        "Tell me a little about your journey "
        "and I'll help you pack smarter."
    )

    with st.form(
        "onboarding_form"
    ):

        col1, col2 = st.columns(2)

        with col1:

            name = st.text_input(
                "👤 Your name",
                placeholder="Enter your name",
            )

            email = st.text_input(
                "📧 Email address",
                placeholder="yourname@example.com",
            )

            destination = st.text_input(
                "📍 Where are you travelling?",
                placeholder="Example: Goa, Dubai, Paris",
            )

        with col2:

            trip_duration = st.number_input(
                "🗓️ How many days?",
                min_value=1,
                max_value=365,
                value=3,
            )

            trip_type = st.selectbox(
                "🎒 What type of trip is this?",
                [
                    "Vacation",
                    "Business",
                    "Adventure",
                    "Family trip",
                    "College trip",
                    "Beach trip",
                    "Other",
                ],
            )

            luggage = st.selectbox(
                "🧳 What luggage are you carrying?",
                [
                    "Backpack",
                    "Cabin bag",
                    "Suitcase",
                    "Large suitcase",
                    "Not decided yet",
                ],
            )

        st.write("")

        submitted = st.form_submit_button(
            "✨ Plan My Trip",
            use_container_width=True,
        )

    if submitted:

        if (
            not name.strip()
            or not email.strip()
            or not destination.strip()
        ):

            st.warning(
                "Please fill in your name, email "
                "and destination."
            )

        else:

            st.session_state.name = name.strip()

            st.session_state.email = email.strip()

            st.session_state.destination = (
                destination.strip()
            )

            st.session_state.trip_duration = (
                trip_duration
            )

            st.session_state.trip_type = trip_type

            st.session_state.luggage = luggage

            st.session_state.chat = create_chat()

            st.session_state.messages = []

            st.session_state.checklist = []

            st.session_state.onboarded = True

            st.rerun()

    st.stop()


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.title("🧳 PackWise AI")

    st.caption(
        "Your intelligent travel packing companion."
    )

    st.divider()

    st.subheader("🗺️ Current Trip")

    st.write(
        f"**👤 Traveler**\n\n"
        f"{st.session_state.name}"
    )

    st.write(
        f"**📍 Destination**\n\n"
        f"{st.session_state.destination}"
    )

    st.write(
        f"**🗓️ Duration**\n\n"
        f"{st.session_state.trip_duration} days"
    )

    st.write(
        f"**🎒 Trip Type**\n\n"
        f"{st.session_state.trip_type}"
    )

    st.write(
        f"**🧳 Luggage**\n\n"
        f"{st.session_state.luggage}"
    )

    st.divider()

    st.subheader("⚡ Quick Actions")

    if st.button(
        "🔄 Start New Trip",
        use_container_width=True,
        key="sidebar_new_trip",
    ):

        start_new_trip()

    st.write("")

    st.caption(
        "PackWise AI uses Gemini to create "
        "personalized travel recommendations."
    )


# =========================================================
# MAIN HEADER
# =========================================================

st.title("🧳 PackWise AI")

st.write(
    f"### Welcome, {st.session_state.name}! 👋"
)

st.caption(
    "Your personal AI travel companion "
    "is ready to help you pack smarter."
)

st.divider()


# =========================================================
# TRIP SNAPSHOT
# =========================================================

st.subheader("✈️ Your Trip Snapshot")

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "📍 Destination",
        st.session_state.destination,
    )

with col2:

    st.metric(
        "🗓️ Duration",
        f"{st.session_state.trip_duration} days",
    )

with col3:

    st.metric(
        "🎒 Trip Type",
        st.session_state.trip_type,
    )

with col4:

    st.metric(
        "🧳 Luggage",
        st.session_state.luggage,
    )


st.write("")

st.info(
    f"💡 **Packing mission:** Prepare for "
    f"{st.session_state.trip_duration} days in "
    f"{st.session_state.destination} with your "
    f"{st.session_state.luggage.lower()}."
)


# =========================================================
# PACKWISE TOOLS
# =========================================================

st.divider()

st.subheader("✨ Your PackWise Tools")

tab1, tab2, tab3 = st.tabs(
    [
        "💬 AI Packing Assistant",
        "🧳 Smart Checklist",
        "📧 Travel Plan",
    ]
)


# =========================================================
# TAB 1 — AI ASSISTANT
# =========================================================

with tab1:

    st.write("### 🤖 Ask PackWise Anything")

    st.caption(
        "Ask about clothes, essentials, weather, "
        "outfits, luggage space or upload a photo "
        "of your items."
    )

    if not st.session_state.messages:

        welcome_message = (
            WELCOME_MESSAGE_TEMPLATE.format(
                name=st.session_state.name
            )
        )

        add_message(
            "assistant",
            "text",
            welcome_message,
        )

    else:

        for message in st.session_state.messages:

            render_message(message)

    st.write("")

    user_input = st.chat_input(
        "Ask about your trip or upload your items 📸",
        accept_file=True,
        file_type=[
            "jpg",
            "jpeg",
            "png",
            "webp",
        ],
        key="packing_chat_input",
    )

    if user_input:

        photo = (
            user_input.files[0]
            if user_input.files
            else None
        )

        text = user_input.text

        parts = []

        # IMAGE

        if photo is not None:

            photo_bytes = photo.getvalue()

            add_message(
                "user",
                "image",
                photo_bytes,
            )

            parts.append(
                types.Part.from_bytes(
                    data=photo_bytes,
                    mime_type=photo.type,
                )
            )

        # TEXT

        if text:

            add_message(
                "user",
                "text",
                text,
            )

            parts.append(text)

        # PHOTO WITHOUT TEXT

        elif photo is not None:

            parts.append(
                """
Analyze the travel items in this photo.

Identify what you can see.

Tell me:

1. What items are present.
2. Which items are useful for my trip.
3. Which items I should pack.
4. Which items I can leave behind.
5. Any important missing items.

Give practical recommendations based on:

- destination
- trip duration
- trip type
- luggage type
"""
            )

        if parts:

            with st.spinner(
                "🧠 PackWise is analyzing your items..."
            ):

                answer = ask_gemini(parts)

            add_message(
                "assistant",
                "text",
                answer,
            )


# =========================================================
# TAB 2 — SMART CHECKLIST
# =========================================================

with tab2:

    st.write("### 🧳 Smart Packing Checklist")

    st.caption(
        "Let AI create a personalized checklist "
        "based on your destination, trip and luggage."
    )

    if st.button(
        "✨ Generate My Packing Checklist",
        use_container_width=True,
        key="generate_packing_checklist",
    ):

        with st.spinner(
            "🧠 Creating your personalized checklist..."
        ):

            checklist = generate_checklist()

            st.session_state.checklist = checklist

            if checklist:

                st.success(
                    f"🎉 Your checklist is ready! "
                    f"{len(checklist)} items to consider."
                )

    if st.session_state.checklist:

        st.write("")

        total_items = len(
            st.session_state.checklist
        )

        completed_items = 0

        left, right = st.columns(2)

        for index, item in enumerate(
            st.session_state.checklist
        ):

            if index % 2 == 0:

                with left:

                    checked = st.checkbox(
                        item,
                        key=f"packing_item_{index}",
                    )

                    if checked:

                        completed_items += 1

            else:

                with right:

                    checked = st.checkbox(
                        item,
                        key=f"packing_item_{index}",
                    )

                    if checked:

                        completed_items += 1

        progress = (
            completed_items / total_items
            if total_items
            else 0
        )

        st.write("")

        st.subheader("📊 Packing Progress")

        st.progress(progress)

        st.write(
            f"**{completed_items} / {total_items} "
            f"items packed**"
        )

        if completed_items == total_items:

            st.success(
                "🎉 Amazing! Everything is packed. "
                "You're ready to travel!"
            )

        elif completed_items > 0:

            remaining = (
                total_items - completed_items
            )

            st.info(
                f"🎒 {remaining} items remaining."
            )

        st.write("")

        if st.button(
            "🗑️ Clear Checklist",
            use_container_width=True,
            key="clear_packing_checklist",
        ):

            st.session_state.checklist = []

            st.rerun()

    else:

        st.info(
            "Your checklist will appear here after "
            "you generate it."
        )


# =========================================================
# TAB 3 — TRAVEL PLAN
# =========================================================

with tab3:
        st.write("### 📧 Save Your Travel Plan")

        st.caption(
            "Get a complete personalized packing plan "
            "delivered to your email."
        )

        st.write("")

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "👤 Traveler",
                st.session_state.name,
            )

        with col2:

            st.metric(
                "📧 Email",
                st.session_state.email,
            )

        st.write("")

        st.info(
            "Your plan will include:\n\n"
            "• Must-pack items\n"
            "• Recommended items\n"
            "• Optional items\n"
            "• Items to leave behind\n"
            "• Suggested outfits\n"
            "• Space-saving tips\n"
            "• Destination tips"
        )

        if st.button(
            "📧 Send My Packing Plan",
            use_container_width=True,
            key="send_packing_plan_email",
        ):

            with st.spinner(
                "🧠 Preparing your personalized travel plan..."
            ):

                try:

                    summary_prompt = f"""
    Create a complete and practical travel packing plan
    for this traveler.

    Traveler name:
    {st.session_state.name}

    Destination:
    {st.session_state.destination}

    Trip duration:
    {st.session_state.trip_duration} days

    Trip type:
    {st.session_state.trip_type}

    Luggage type:
    {st.session_state.luggage}

    {SUMMARY_REQUEST_PROMPT}

    Use the conversation above to personalize the plan.

    Make the email easy to read with clear sections:

    - Must-pack items
    - Recommended items
    - Optional items
    - Items to leave behind
    - Suggested outfits
    - Space-saving tips
    - Important destination tips

    Keep it practical, friendly and concise.

    Do not use markdown tables.
    """

                    summary = ask_gemini(
                        [summary_prompt]
                    )

                    if summary.startswith(
                        "Sorry, something went wrong:"
                    ):

                        st.error(summary)

                    else:

                        send_email(
                            st.session_state.email,
                            "🧳 Your PackWise AI Travel Plan",
                            summary,
                        )

                        st.success(
                            "✅ Your personalized packing "
                            "plan has been sent!"
                        )

                        st.info(
                            f"📧 Check: "
                            f"{st.session_state.email}"
                        )

                        st.caption(
                            "💡 If you don't see it in your "
                            "inbox, check Spam/Junk."
                        )

                except Exception as error:

                    st.error(
                        f"❌ Unable to send email: {error}"
                    )



# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "🧳 PackWise AI • "
    "Pack less. Travel smarter. Explore better. 🌎"
)