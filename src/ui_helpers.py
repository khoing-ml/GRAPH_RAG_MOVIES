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


def inject_gemini_styles():
    """Inject Gemini-inspired CSS for a clean, centered chat UI."""
    dark = st.session_state.get('dark_mode', True)
    
    # Gemini-like color scheme
    if dark:
        page_bg = '#141414'
        chat_bg = '#1e1e1e'
        assistant_bg = '#262626'
        user_bg = '#1e40af'  # Blue from Gemini
        text_color = '#ffffff'
        text_secondary = '#e0e0e0'
    else:
        page_bg = '#ffffff'
        chat_bg = '#f5f5f5'
        assistant_bg = '#f0f0f0'
        user_bg = '#1e40af'
        text_color = '#000000'
        text_secondary = '#666666'

    css = f"""
    <style>
    :root {{
        --page-bg: {page_bg};
        --chat-bg: {chat_bg};
        --assistant-bg: {assistant_bg};
        --user-bg: {user_bg};
        --text-color: {text_color};
        --text-secondary: {text_secondary};
    }}
    
    * {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }}
    
    .stApp {{
        background-color: var(--page-bg);
        color: var(--text-color);
    }}
    
    /* Remove top padding and default streamlit styling */
    .main {{
        padding-top: 2rem !important;
    }}
    
    /* Chat container styling */
    .chat-wrapper {{
        display: block;
        margin-bottom: 180px;
        max-width: 900px;
        margin-left: auto;
        margin-right: auto;
        padding: 0 20px;
    }}
    
    .chat-scroll {{
        height: auto;
        overflow: visible;
        padding: 20px 0;
        background: transparent;
    }}
    
    /* Message bubbles */
    .message {{
        display: flex;
        margin: 16px 0;
        align-items: flex-end;
        animation: fadeIn 0.3s ease-in;
    }}
    
    @keyframes fadeIn {{
        from {{
            opacity: 0;
            transform: translateY(10px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    .message.assistant {{
        justify-content: flex-start;
    }}
    
    .message.user {{
        justify-content: flex-end;
    }}
    
    .avatar {{
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-right: 12px;
        flex: 0 0 32px;
        font-size: 18px;
        background: rgba(255,255,255,0.1);
    }}
    
    .bubble {{
        max-width: 75%;
        padding: 12px 16px;
        border-radius: 18px;
        line-height: 1.5;
        word-wrap: break-word;
        font-size: 15px;
    }}
    
    .message.assistant .bubble {{
        background-color: var(--assistant-bg);
        color: var(--text-color);
        border-radius: 18px 18px 18px 4px;
    }}
    
    .message.user .bubble {{
        background-color: var(--user-bg);
        color: white;
        border-radius: 18px 18px 4px 18px;
    }}
    
    /* Form styling */
    form.stForm {{
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        width: 90%;
        max-width: 800px;
        z-index: 100;
        background: transparent;
        border: none;
        padding: 0;
    }}
    
    form.stForm > div {{
        background: transparent !important;
        border: none !important;
    }}
    
    .stTextArea {{
        width: 100% !important;
    }}
    
    textarea[role='textbox'] {{
        background-color: var(--chat-bg) !important;
        color: var(--text-color) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 24px !important;
        padding: 12px 16px !important;
        font-size: 15px !important;
        resize: none !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
        transition: all 0.2s ease !important;
    }}
    
    textarea[role='textbox']:focus {{
        outline: none !important;
        border-color: var(--user-bg) !important;
        box-shadow: 0 4px 12px rgba(30,64,175,0.3) !important;
    }}
    
    button[kind='primary'] {{
        background-color: var(--user-bg) !important;
        color: white !important;
        border: none !important;
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
        padding: 0 !important;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.2s ease !important;
    }}
    
    button[kind='primary']:hover {{
        background-color: #1e3a8a !important;
        box-shadow: 0 4px 12px rgba(30,64,175,0.4) !important;
    }}
    
    /* Hide default Streamlit elements */
    .stDeployButton {{
        visibility: hidden;
    }}
    
    #MainMenu {{
        visibility: hidden;
    }}
    
    footer {{
        visibility: hidden;
    }}
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {{
        width: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: transparent;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: rgba(255,255,255,0.2);
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: rgba(255,255,255,0.3);
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_chat_messages(messages):
    """Render chat messages in Gemini-style bubbles."""
    inject_gemini_styles()
    
    if not messages:
        return
    
    html = ["<div class='chat-wrapper'><div class='chat-scroll'>"]
    
    for m in messages:
        role = m.get('role', 'assistant')
        content = m.get('content', '')
        
        # Escape HTML and convert newlines
        content_html = str(content).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
        
        if role == 'user':
            html.append(
                f"<div class='message user'><div class='bubble'>{content_html}</div></div>"
            )
        else:
            html.append(
                f"<div class='message assistant'><div class='avatar'>🤖</div><div class='bubble'>{content_html}</div></div>"
            )
    
    html.append("</div></div>")
    st.markdown('\n'.join(html), unsafe_allow_html=True)
