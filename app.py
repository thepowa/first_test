"""
This file is part of the langchain-kr project.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

This file references code from the following source:
Link: https://github.com/teddylee777/langchain-kr

Original Author: teddylee777
Modifications:
- [2024-07-23]: Added and modified some comments for clarification and added a docstring by jonhyuk0922

"""

import streamlit as st
from utils import init_conversation, print_conversation ,StreamHandler
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import ChatMessage
from langchain_core.runnables.history import RunnableWithMessageHistory  # history 와 현재 입력으로 들어오는(runnable) 메세지 같이 실행할 수 있도록 하는 기능
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_upstage import ChatUpstage


from dotenv import load_dotenv
import os

# 페이지 표시 및 타이틀 입력
st.set_page_config(page_title="EMT_field_chatbot",page_icon="🍀")
st.title("🍀 EMT_field_chatbot 🍀")

# dotenv 로 key 불러오기
load_dotenv()

# Redis 서버의 URL을 지정합니다.
REDIS_URL = "redis://localhost:6379/0"

# LANGCHAIN_TRACING_V2 환경 변수를 "true"로 설정합니다.
os.environ["LANGCHAIN_TRACING_V2"] = "true"
# LANGCHAIN_PROJECT 설정
os.environ["LANGCHAIN_PROJECT"] = "RunnableWithMessageHistory"

# 채팅 대화기록을 저장하는 store를 session_state 저장
if "store" not in st.session_state:
    st.session_state["store"] = dict()

def get_redis_message_history(session_id: str) -> RedisChatMessageHistory:
    # 세션 ID를 기반으로 RedisChatMessageHistory 객체를 반환합니다.
    return RedisChatMessageHistory(session_id, url=REDIS_URL)

# session_id 직접 입력하도록 하기
with st.sidebar:
    session_id = st.text_input("session ID",value="ssac0724")

    clear_space = st.button("대화기록 초기화")
    if clear_space:
        st.session_state["messages"] = []
        st.rerun()

# session state 에 메세지 초기화 및 대화 출력
init_conversation()
print_conversation()

# store = {}  # 세션 기록을 저장할 딕셔너리
# # => 이러한 형태는 인메모리, 즉 이 파일이 꺼지면 메모리가 사라진다. 

# session id 기반으로 이전 세션기록 불러오기
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """지정된 세션 ID에 해당하는 채팅 기록을 반환합니다.

    세션 ID가 store에 존재하지 않으면 새로운 ChatMessageHistory 객체를 생성하여 store에 저장합니다.
    
    Args:
        session_ids (str):  세션 ID 문자열

    Returns:
        BaseChatMessageHistory: 지정된 세션 ID에 해당하는 채팅 기록 객체
    """
    if session_id not in st.session_state["store"]:
        # 새로운 ChatMessageHistory 객체 생성하여 store에 저장
        st.session_state["store"][session_id] = ChatMessageHistory()
    return st.session_state["store"][session_id]  # session id 에 해당하는 세션 기록 반환

# 유저 입력 받아와서 챗봇 메세지로 기록 
if user_input:= st.chat_input("텍스트를 입력하세요."):
    # print(type(prompt)) # str
    st.chat_message("user").write(f"{user_input}")
    st.session_state["messages"].append(ChatMessage(role="user",content=user_input))
    
    # assistant 답변 표시 및 저장하기
    with st.chat_message("assistant"):
        stream_handler = StreamHandler(st.empty())  # container = st.empty() 로 만든 공간 = 들어온 메세지를 찍어내는 공간

        # 1. LLM 모델 생성
        llm = ChatUpstage(streaming=True, callbacks=[stream_handler],model='solar-mini')

        # 2. 질문-답변 체인 생성
        qa_system_prompt = """현장 응급의료 업무를 돕는 전문가입니다. 질문에 답하기 위해 검색된 내용을 사용하세요. 답변은 세 문장 이내로 간결하게 유지하세요.
            ## 답변 예시
            📍답변 내용:
            {context}"""

        qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
        )
        runnable = qa_prompt | llm  # 프롬프트와 모델을 연결하여 runnable 객체 생성

        # 3. 답변 생성하기
        chain_with_memory = RunnableWithMessageHistory(
            runnable,  # 실행할 Runnable 객체
            get_redis_message_history,  # redis 에 세션 기록
            input_messages_key="question",  # 입력 질문의 키
            history_messages_key="history",  # 기록 메시지의 키
            )
        print("잘들어가고 있나",session_id)
        response = chain_with_memory.invoke({
            # 시스템 프롬프트의 {text} 변수에 들어갈 값
            "text": "환자가 의식이 없어서 지혈만 하고 병원으로 이송했다.",
            
            # 시스템 프롬프트의 {context} 변수에 들어갈 값
            "context": "응급의료법 관련 프로토콜 내용", 
            
            # Human 메시지의 {input} 변수에 들어갈 값 (사용자의 실제 질문)
            "input": user_input, 
            
            # MessagesPlaceholder("chat_history")에 들어갈 값 (이전 대화 기록)
            "chat_history": st.session_state.messages 
        },
            # 설정 정보로 세션 ID "ssac0724"를 전달합니다.
            config={"configurable": {"session_id": session_id}},
        )
        st.session_state["messages"].append(ChatMessage(role="assistant",content=response.content))