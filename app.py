import os
import hashlib
import hmac
import random
import time
from datetime import datetime, timezone, date
import streamlit as st

st.set_page_config(page_title="For Roz ♡", page_icon="🌹", layout="centered", initial_sidebar_state="collapsed")

# Shared messages require Supabase credentials in Streamlit secrets or environment variables.
def setting(name, default=""):
    try:
        value = st.secrets.get(name, default)
        if value:
            return value
    except Exception:
        pass
    return os.getenv(name, default)

SUPABASE_URL = setting("SUPABASE_URL").rstrip("/")
SUPABASE_KEY = setting("SUPABASE_KEY")
ROOM_PASSWORD_HASH = setting("ROOM_PASSWORD_HASH")
SHARED_READY = bool(SUPABASE_URL and SUPABASE_KEY)

try:
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_KEY) if SHARED_READY else None
except Exception:
    sb = None
    SHARED_READY = False

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@400;500;600&display=swap');
:root { --rose:#d9a0b7; --pink:#f0c5d4; --ink:#0b0a10; }
.stApp {background:radial-gradient(ellipse at 50% 0%,#21192b 0%,#0b0a10 53%,#08080d 100%); color:#f4e7eb;}
html, body, [class*="css"] {font-family:'DM Sans',sans-serif;}
h1,h2,h3,.serif {font-family:'Playfair Display',serif!important;}
.block-container {max-width:780px;padding-top:1.2rem;padding-bottom:4rem;}
div[data-testid="stVerticalBlockBorderWrapper"] {border-color:#3a2a3a!important;border-radius:22px!important;background:rgba(25,21,31,.78);}
.stButton>button {border:1px solid #87516d;background:linear-gradient(135deg,#743d59,#512b43);color:#fff;border-radius:999px;padding:.62rem 1.1rem;min-height:2.8rem;}
.stButton>button:hover {border-color:#e5b5c8;color:white;background:#77425d;}
.stTextInput input,.stTextArea textarea,.stSelectbox div[data-baseweb="select"] {background:#171520!important;color:#f4e7eb!important;border-radius:12px!important;border-color:#453347!important;}
div[data-testid="stAlert"] {border-radius:14px;}
.hero {border:1px solid #493447;border-radius:30px;padding:2.6rem 1.3rem;text-align:center;background:radial-gradient(ellipse at center,#211a2b 0%,#14121d 65%,#111018 100%);margin-bottom:1.2rem;}
.eyebrow {letter-spacing:.24em;text-transform:uppercase;color:#d9a0b7;font-size:.72rem;}
.hero h1 {font-size:clamp(3.4rem,11vw,5.5rem);font-weight:500;line-height:1.1;margin:.6rem 0 1rem;color:#f4e7eb;}
.sub {color:#c7bacb;font-size:1.06rem;line-height:1.85;max-width:540px;margin:auto;}
.petal {color:#d9a0b7;letter-spacing:.5em;font-size:1.3rem;margin-top:1.4rem;}
.card {padding:1.1rem 1.2rem;border:1px solid #382b3a;border-radius:20px;background:rgba(24,21,31,.85);margin:.4rem 0;}
.msg {padding:1rem 1.1rem;border:1px solid #493347;border-radius:18px;background:#17141e;margin:.55rem 0;overflow-wrap:anywhere;}
.msg small {color:#b49caf;}
.quote {font-family:'Playfair Display',serif;font-size:1.55rem;line-height:1.6;text-align:center;color:#f1dbe4;padding:1.2rem .3rem;}
div[data-testid="stTabs"] button {color:#e8dce6;}
hr {border-color:#342735;}
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

SURPRISES = [
    ("🌹 A tiny truth", "Some people become a small, unexpected corner of your mind. That doesn't mean you have to rush the story."),
    ("👀 Your turn", "What's one question you've wanted to ask me but never found the right moment for?"),
    ("🌙 Midnight thought", "If tonight had a colour, what colour would it be — and why?"),
    ("🎲 Friendly dare", "Send a song that matches your mood right now. No explanation required. Yet. 😌"),
    ("💌 A little note", "No pressure to be interesting, funny, or okay all the time. Just show up as yourself."),
    ("🫣 NGL prompt", "What's a first impression you had of me that changed later?"),
    ("📚 Bookish chaos", "Pick one: read each other's favourite book, exchange playlists, or talk until 3 AM?"),
    ("✨ Soft reminder", "Curiosity isn't a promise. Be honest, be kind, and let things unfold at their own pace."),
    ("🥹 Tiny compliment", "Your existence doesn't need to be explained or earned to be worth appreciating."),
    ("🕯️ One honest sentence", "Finish this: “Something I wish people understood about me is…”"),
]
QUESTIONS = {
    "Cute": ["What's a tiny thing that can instantly improve your day?", "What kind of message makes you smile at your phone?", "What's a small thing you remember about people?"],
    "Deep": ["What's something people often misunderstand about you?", "When do you feel most like yourself?", "What's a lesson life taught you the hard way?"],
    "Chaotic": ["What's your most questionable opinion?", "What's a harmless hill you'll die on?", "What fictional character would be your worst roommate?"],
    "NGL": ["What's something you've wanted to ask me?", "What was your first impression of me?", "What's one thing you find hard to say out loud?"],
    "Late night": ["What's a thought you can't explain?", "If you could revisit one ordinary day, which would it be?", "What song feels like a memory?"],
}
REACTIONS = ["❤️", "😂", "🥹", "👀", "🌹"]

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def get_messages():
    if not sb:
        return []
    try:
        res = sb.table("roz_messages").select("*").eq("room_id", st.session_state.room_id).order("created_at", desc=True).limit(100).execute()
        return res.data or []
    except Exception as e:
        st.error("Could not load shared messages. Check your Supabase setup and table SQL.")
        return []

def send_message(kind, text, sender, reply_to=None):
    if not sb:
        return False
    try:
        payload = {"room_id": st.session_state.room_id, "sender": sender, "kind": kind, "body": text.strip(), "reply_to": reply_to, "created_at": utcnow()}
        sb.table("roz_messages").insert(payload).execute()
        return True
    except Exception:
        st.error("Message wasn't sent. Check the database setup, then try again.")
        return False

def update_reaction(message_id, reaction, current):
    if not sb:
        return
    # Reaction rows are stored separately so multiple visitors can react.
    try:
        sb.table("roz_reactions").insert({"message_id": message_id, "room_id": st.session_state.room_id, "reactor": st.session_state.get("visitor_name","Guest"), "reaction": reaction}).execute()
    except Exception:
        st.info("Reactions need the roz_reactions table from supabase_schema.sql.")

def unlock_room():
    st.session_state.room_unlocked = True
    st.session_state.room_id = "main"
    st.session_state.visitor_name = st.session_state.get("visitor_name_input", "Guest").strip()[:24] or "Guest"

if "room_unlocked" not in st.session_state:
    st.session_state.room_unlocked = False
if "visitor_name" not in st.session_state:
    st.session_state.visitor_name = "Guest"

st.markdown("""
<div class="hero">
 <div class="eyebrow">a little place on the internet</div>
 <h1>hey, Roz. ♡</h1>
 <div class="sub">A tiny world for messages, questions, little chaos, and things that are easier to type than to say.</div>
 <div class="petal">☾ ✦ 🌹 ✦ ☾</div>
</div>
""", unsafe_allow_html=True)

if not SHARED_READY:
    st.warning("Shared chat is not connected yet. The site can show its playful features, but messages between phones need a Supabase database and secrets configured.")
    with st.expander("Set up shared messages (one-time setup)", expanded=True):
        st.markdown("1. Create a free project at [Supabase](https://supabase.com/).  2. Open **SQL Editor** and run the included `supabase_schema.sql`.  3. Copy the Project URL and `service_role` key from Project Settings → API.  4. Add them as Streamlit secrets.")
        st.code('SUPABASE_URL = "https://YOUR-PROJECT.supabase.co"\nSUPABASE_KEY = "YOUR_SERVICE_ROLE_KEY"\nROOM_PASSWORD_HASH = "optional-sha256-hash"', language="toml")
        st.caption("Keep the service-role key secret. Never put it in a public GitHub file. The included README explains deployment.")
    # Continue showing the demo UI, but do not imply messages are shared.
else:
    if not st.session_state.room_unlocked:
        with st.container(border=True):
            st.subheader("🔐 The little private room")
            st.write("Enter the room code/password you both agreed on.")
            st.text_input("Your nickname", key="visitor_name_input", placeholder="Your name or nickname")
            room_pass = st.text_input("Room code / password", type="password", placeholder="Only share this with the person you trust")
            if st.button("Enter our little world ♡", use_container_width=True):
                valid = False
                if ROOM_PASSWORD_HASH:
                    valid = hmac.compare_digest(hashlib.sha256(room_pass.encode()).hexdigest(), ROOM_PASSWORD_HASH.strip().lower())
                else:
                    st.error("Set ROOM_PASSWORD_HASH in Streamlit secrets first. Generate it with: python -c \"import hashlib; print(hashlib.sha256(b'YOUR_ROOM_PASSWORD').hexdigest())\"")
                if valid:
                    unlock_room()
                    st.rerun()
                elif ROOM_PASSWORD_HASH:
                    st.error("That code doesn't match. Try again.")
        st.stop()
    else:
        st.caption(f"You're in as **{st.session_state.visitor_name}** · shared room")
        if st.button("Lock room", key="lock_room"):
            st.session_state.room_unlocked = False
            st.rerun()

tabs = st.tabs(["💬 NGL corner", "😜 Surprise me", "🎲 Ask anything", "💌 Message bottle", "🌹 Rose garden", "🌙 Midnight"])

with tabs[0]:
    st.subheader("NGL corner")
    st.caption("Leave a note, ask something, or reply. Don't share sensitive secrets here.")
    sender = st.text_input("Post as", value=st.session_state.visitor_name, key="sender_name", max_chars=24)
    kind = st.selectbox("What kind of message?", ["NGL", "Question", "Confession", "Just saying", "Song / memory"])
    body = st.text_area("Your message", placeholder="Type it here… 👀", height=110, max_chars=1200, key="new_message")
    if st.button("Send to our room 💌", use_container_width=True):
        if not body.strip():
            st.warning("Write a few words first.")
        elif not SHARED_READY or not st.session_state.room_unlocked:
            st.info("Connect Supabase and unlock the room to send messages between phones.")
        elif send_message(kind, body, sender or "Guest"):
            st.success("Left in your little room. ♡"
            st.rerun()
    st.markdown("---")
    st.markdown("#### Recent messages")
    if SHARED_READY and st.session_state.room_unlocked:
        if st.button("↻ Refresh messages"):
            st.rerun()
        messages = get_messages()
        if not messages:
            st.info("No notes yet. Someone gets to be the first. 👀")
        for msg in messages:
            st.markdown(f"""<div class="msg"><small>{msg.get('kind','Note')} · {msg.get('sender','Guest')} · {str(msg.get('created_at',''))[:16].replace('T',' ')}</small><br><div style="white-space:pre-wrap;margin-top:.5rem">{__import__('html').escape(msg.get('body',''))}</div></div>""", unsafe_allow_html=True)
            cols = st.columns([1,1,1,2])
            for i, reaction in enumerate(REACTIONS[:3]):
                if cols[i].button(reaction, key=f"react_{msg['id']}_{reaction}"):
                    update_reaction(msg["id"], reaction, None)
                    st.toast("Reaction added (if reactions table is set up).")
            with cols[3]:
                if st.button("Reply ↩", key=f"reply_{msg['id']}"):
                    st.session_state.reply_to = msg["id"]
                    st.session_state.reply_body = ""
            if st.session_state.get("reply_to") == msg["id"]:
                reply = st.text_input("Your reply", key=f"reply_input_{msg['id']}")
                if st.button("Send reply", key=f"reply_send_{msg['id']}"):
                    if reply.strip() and send_message("Reply", reply, sender or "Guest", msg["id"]):
                        st.session_state.reply_to = None
                        st.success("Reply sent.")
                        st.rerun()
    else:
        st.info("This section becomes a real shared message wall after Supabase is connected and the room is unlocked.")

with tabs[1]:
    st.subheader("CLICK HERE 😜")
    st.write("No spoilers. Just tap.")
    if "surprise" not in st.session_state:
        st.session_state.surprise = random.choice(SURPRISES)
    if st.button("Open a random surprise ✨", use_container_width=True):
        pool = [x for x in SURPRISES if x != st.session_state.surprise] or SURPRISES
        st.session_state.surprise = random.choice(pool)
    title, content = st.session_state.surprise
    st.markdown(f'<div class="card"><div style="color:#d9a0b7;font-size:1.1rem">{title}</div><div style="font-size:1.08rem;line-height:1.8;margin-top:.7rem">{content}</div></div>', unsafe_allow_html=True)
    st.caption("A fresh surprise each click. Save the good ones in a message.")

with tabs[2]:
    st.subheader("Ask anything 👀")
    category = st.radio("Pick a vibe", list(QUESTIONS), horizontal=True)
    if st.button("Give me a question 🎲"):
        st.session_state.question = random.choice(QUESTIONS[category])
    if "question" not in st.session_state:
        st.session_state.question = random.choice(QUESTIONS["NGL"])
    st.markdown(f'<div class="quote">“{st.session_state.question}”</div>', unsafe_allow_html=True)
    answer = st.text_area("Your answer", key="answer", placeholder="No perfect answer needed…")
    if st.button("Post answer to our room"):
        if not answer.strip():
            st.warning("Write an answer first.")
        elif SHARED_READY and st.session_state.room_unlocked:
            if send_message(f"Question · {category}", f"{st.session_state.question}\n\n{answer}", st.session_state.visitor_name):
                st.success("Answer posted.")
                st.rerun()
        else:
            st.info("Connect and unlock the shared room to post answers.")

with tabs[3]:
    st.subheader("Message in a bottle 🕯️")
    st.write("Write a note for later. This starter version stores the scheduled note in this browser session only; it is not a secure, cross-device timed delivery.")
    bottle = st.text_area("Your sealed note", placeholder="Open this when…", key="bottle_text")
    open_on = st.date_input("Choose an opening date", value=date.today())
    if st.button("Seal the bottle"):
        if not bottle.strip():
            st.warning("Write a note first.")
        elif open_on > date.today():
            st.session_state.bottle = {"text": bottle.strip(), "date": open_on.isoformat()}
            st.success("Sealed in this session. Keep this browser session open.")
        else:
            st.info("For a future opening, choose a date after today.")
    if st.session_state.get("bottle"):
        saved = st.session_state.bottle
        if date.today().isoformat() >= saved["date"]:
            st.markdown(f'<div class="card"><b>🕯️ Your bottle is open</b><p style="white-space:pre-wrap">{__import__("html").escape(saved["text"])}</p></div>', unsafe_allow_html=True)
        else:
            st.info(f"🔒 Sealed until {saved['date']}.")

with tabs[4]:
    st.subheader("The rose garden 🌹")
    st.write("Tap a rose to reveal a little thought.")
    garden = [
        ("🌹", "A rose for the things you almost said.", "Not every thought needs a perfect ending."),
        ("🥀", "A rose for an ordinary day.", "Sometimes the smallest moments are the ones that stay."),
        ("🌹", "A rose for a question.", "What is one thing you'd like us to understand about each other?"),
        ("🌷", "A rose for a song.", "Share a song and let the other person guess why you chose it."),
        ("🌹", "A rose for a little courage.", "Honesty can be gentle. It doesn't need to demand anything."),
    ]
    cols = st.columns(5)
    for i, (emoji, label, reveal) in enumerate(garden):
        if cols[i].button(emoji, key=f"rose_{i}", help=label):
            st.session_state[f"rose_reveal_{i}"] = True
    for i, (emoji, label, reveal) in enumerate(garden):
        if st.session_state.get(f"rose_reveal_{i}"):
            st.markdown(f'<div class="card"><b>{label}</b><p>{reveal}</p></div>', unsafe_allow_html=True)

with tabs[5]:
    st.subheader("After midnight ☾")
    st.markdown('<div class="quote">“What is one thought you only seem to have when the world gets quiet?”</div>', unsafe_allow_html=True)
    mood = st.select_slider("What's the vibe tonight?", options=["🌧️ Heavy", "🌫️ Unsure", "🪻 Quiet", "🌙 Thoughtful", "✨ Hopeful", "🎉 Chaotic"], value="🌙 Thoughtful")
    thought = st.text_area("Leave a thought (optional)", placeholder="The 2 AM version of you can write here…", key="midnight_thought")
    if st.button("Keep this thought"):
        if thought.strip() and SHARED_READY and st.session_state.room_unlocked:
            if send_message(f"Midnight · {mood}", thought, st.session_state.visitor_name):
                st.success("Saved to the shared room.")
        elif thought.strip():
            st.session_state.midnight_saved = {"mood": mood, "thought": thought}
            st.success("Kept in this session only. Connect the shared room to send it across phones.")
        else:
            st.info(f"Tonight's mood: {mood}. You don't have to write anything.")

st.markdown("---")
st.markdown('<p style="text-align:center;color:#938699;font-size:.86rem;line-height:1.8">Made as a small, respectful corner of the internet. Only share this room code with someone you trust. A shared link is not the same as true private hosting.</p>', unsafe_allow_html=True)
