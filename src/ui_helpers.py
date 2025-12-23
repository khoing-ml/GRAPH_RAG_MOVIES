import streamlit as st


def render_search_results(results):
    """Render a list of search results (from Qdrant). Return selected movie id."""
    if not results:
        st.info("Không có kết quả nào.")
        return None

    cols = st.columns([4,1])
    sel = None
    for i, hit in enumerate(results):
        payload = getattr(hit, 'payload', {})
        title = payload.get('title') or payload.get('name') or 'Unknown'
        year = payload.get('year') or payload.get('release_year') or ''
        genres = payload.get('genres', [])
        with cols[0]:
            st.markdown(f"**{i+1}. {title}** {f'({year})' if year else ''}")
            if genres:
                st.caption(', '.join(genres))
        with cols[1]:
            if st.button(f"View {i+1}", key=f"view_{i}"):
                sel = payload.get('tmdb_id') or payload.get('id') or payload.get('movie_id')
    return sel


def render_movie_detail(detail):
    if not detail:
        st.info("Không có thông tin chi tiết.")
        return
    # detail is expected to be a dict or plaintext
    if isinstance(detail, dict):
        st.header(detail.get('title') or detail.get('name', 'Chi tiết phim'))
        st.write(f"**Year:** {detail.get('year') or detail.get('release_year', 'N/A')}")
        if detail.get('genres'):
            st.write(f"**Genres:** {', '.join(detail.get('genres'))}")
        if detail.get('overview'):
            st.markdown("**Overview**")
            st.write(detail.get('overview'))
        if detail.get('cast'):
            st.write(f"**Cast:** {', '.join(detail.get('cast'))}")
    else:
        st.write(detail)


def inject_chat_styles():
    dark = st.session_state.get('dark_mode', False)
    # Colors
    bg = '#0f172a' if dark else '#f7f7f8'
    page_bg = '#020617' if dark else '#ffffff'
    assistant_bg = '#374151' if dark else '#eef2ff'
    user_bg = '#111827' if dark else '#111827'
    text_color = '#e6eef8' if dark else '#111827'

    css = f"""
    <style>
    :root {{ --page-bg: {page_bg}; --chat-bg: {bg}; --assistant-bg: {assistant_bg}; --user-bg: {user_bg}; --text-color: {text_color}; }}
    .stApp {{ background: var(--page-bg); }}
    .chat-container{{max-height:65vh;overflow:auto;padding:12px;border-radius:12px;background:var(--chat-bg);box-shadow: 0 2px 8px rgba(0,0,0,0.06)}}
    .message{{display:flex;margin:10px 0;align-items:flex-end}}
    .message.assistant{{justify-content:flex-start}}
    .message.user{{justify-content:flex-end}}
    .avatar{{width:40px;height:40px;border-radius:50%;display:inline-block;margin:0 8px;flex:0 0 40px}}
    .bubble{{max-width:78%;padding:12px 16px;border-radius:16px;line-height:1.45;color:var(--text-color);font-family:Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial}}
    .assistant .bubble{{background:var(--assistant-bg);color:var(--text-color);border-bottom-left-radius:6px}}
    .user .bubble{{background:var(--user-bg);color:white;border-bottom-right-radius:6px}}
    .meta{{font-size:11px;color:rgba(0,0,0,0.45);margin-top:6px}}
    .assistant .meta{{color:rgba(255,255,255,0.6)}}
    /* scrollbar */
    .chat-container::-webkit-scrollbar {{ width:8px }}
    .chat-container::-webkit-scrollbar-thumb {{ background: rgba(0,0,0,0.12); border-radius:8px }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_chat_messages(messages):
    """Render chat messages list using simple HTML bubbles."""
    inject_chat_styles()
    if not messages:
        st.markdown("<div class='chat-container'>No messages yet.</div>", unsafe_allow_html=True)
        return
    html = ["<div class='chat-container'>"]
    for m in messages:
        role = m.get('role', 'assistant')
        content = m.get('content', '')
        time_str = m.get('time', '')
        # basic newline -> <br>
        content_html = str(content).replace('\n', '<br>')
        if role == 'user':
            html.append(
                "<div class='message user'><div class='bubble'>{content}</div></div>".format(content=content_html)
            )
        else:
            html.append(
                "<div class='message assistant'><div class='avatar'>🤖</div><div class='bubble'>{content}</div></div>".format(content=content_html)
            )
    html.append("</div>")
    st.markdown('\n'.join(html), unsafe_allow_html=True)
