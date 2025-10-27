"""Floating Chatbot Component with HKBU GenAI"""
import streamlit as st
import services.ai_service as ai_service
from datetime import datetime

def render_chatbot():
    """Render chatbot UI that appears on all pages when logged in"""
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'chatbot_open' not in st.session_state:
        st.session_state.chatbot_open = False

def render_chatbot_popup():
    """Render chatbot popup when opened from sidebar"""
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Add CSS for better popup styling
    st.markdown("""
    <style>
    .chatbot-popup {
        background: white;
        border: 3px solid #667eea;
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
        box-shadow: 0 15px 40px rgba(0,0,0,0.3);
    }
    .chat-messages-box {
        background: #f8f9fa;
        border: 2px solid #667eea;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        min-height: 300px;
        max-height: 500px;
        overflow-y: auto;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create a container for the popup
    with st.container():
        # Header with close button
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown("### 🤖 AI Assistant")
        with col2:
            if st.button("🗑️ Clear", key="clear_chat_popup", help="Clear chat history"):
                st.session_state.chat_history = []
                st.rerun()
        with col3:
            if st.button("✕ Close", key="close_chatbot_popup"):
                st.session_state.chatbot_open = False
                st.rerun()
        
        st.markdown("---")
        
        # Chat messages area with box styling
        st.markdown('<div class="chat-messages-box">', unsafe_allow_html=True)
        
        # Display chat history
        if st.session_state.chat_history:
            for msg in st.session_state.chat_history:
                if msg['role'] == 'user':
                    with st.chat_message("user"):
                        st.write(msg['content'])
                else:
                    with st.chat_message("assistant"):
                        st.write(msg['content'])
        else:
            # Welcome message
            with st.chat_message("assistant"):
                st.write("👋 Hello! I'm your AI assistant. Ask me anything about stocks, investing, or portfolio management!")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        # Chat input
        user_input = st.chat_input("Type your message here...", key="chat_input_popup")
        
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
