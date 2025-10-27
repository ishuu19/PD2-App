"""Floating Chatbot Component with HKBU GenAI"""
import streamlit as st
import services.ai_service as ai_service
from datetime import datetime

def render_chatbot():
    """Render floating chatbot UI that appears on all pages when logged in"""
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'chatbot_open' not in st.session_state:
        st.session_state.chatbot_open = False
    
    # CSS for chatbot styling
    st.markdown("""
    <style>
    /* Floating Chat Container */
    .chatbot-container {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
    }
    
    /* Toggle Button */
    .chat-toggle {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 50%;
        width: 60px;
        height: 60px;
        font-size: 28px;
        cursor: pointer;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
        transition: all 0.3s ease;
    }
    
    .chat-toggle:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 25px rgba(102, 126, 234, 0.6);
    }
    
    /* Chat Window */
    .chat-window {
        position: fixed;
        bottom: 90px;
        right: 20px;
        width: 400px;
        max-height: 500px;
        background: white;
        border-radius: 15px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        z-index: 999;
        overflow: hidden;
    }
    
    .chat-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Hide empty space */
    .stChatFloatingInputContainer {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Floating toggle button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col3:
        if st.button("💬", key="toggle_chat", help="Toggle Chatbot", use_container_width=False):
            st.session_state.chatbot_open = not st.session_state.chatbot_open
            st.rerun()
    
    # Show chatbot window when open
    if st.session_state.chatbot_open:
        with st.container():
            # Chat Header
            header_col1, header_col2 = st.columns([5, 1])
            with header_col1:
                st.markdown("""
                <div class="chat-header">
                    <strong>🤖 AI Assistant</strong>
                </div>
                """, unsafe_allow_html=True)
            with header_col2:
                if st.button("✕", key="close_chat"):
                    st.session_state.chatbot_open = False
                    st.rerun()
            
            # Chat messages
            if st.session_state.chat_history:
                for msg in st.session_state.chat_history:
                    with st.chat_message(msg['role']):
                        st.markdown(msg['content'])
            else:
                st.info("👋 Hello! I'm your AI assistant. Ask me anything about stocks, investing, or portfolio management!")
            
            # Chat input
            user_input = st.chat_input("Type your message here...", key="chat_input_main")
            
            if user_input:
                # Add user message
                st.session_state.chat_history.append({
                    'role': 'user',
                    'content': user_input,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Get AI response
                with st.spinner("🤔 AI is thinking..."):
                    system_prompt = """You are a helpful financial AI assistant for a stock portfolio management platform. 
                    Provide clear, concise, and informative answers about stocks, investing, and portfolio management.
                    Be friendly, professional, and helpful. If asked about specific stocks, provide general insights
                    but remind users to do their own research."""
                    
                    response = ai_service.get_ai_response(
                        prompt=user_input,
                        system_prompt=system_prompt,
                        max_tokens=500,
                        temperature=0.7
                    )
                    
                    # Add AI response
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': response,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Keep only last 20 messages
                    if len(st.session_state.chat_history) > 20:
                        st.session_state.chat_history = st.session_state.chat_history[-20:]
                    
                    st.rerun()
