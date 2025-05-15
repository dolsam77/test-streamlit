import streamlit as st
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI
from langchain import hub
from langchain.chains import RetrievalQA
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

st.set_page_config(page_title="소득세 챗봇", page_icon="🤖")

st.title("📊 Streamlit 기본 예제")
st.caption("소득세에 관련되 모든것을 답변해 드립니다.")
load_dotenv()

if "message_list" not in st.session_state:
  st.session_state.message_list = []

for message in st.session_state.message_list:
  with st.chat_message(message["role"]):
    st.write(message["content"])
    
def get_ai_message(user_message):  #===> 추가 부분
 
  embedding = OpenAIEmbeddings(model='text-embedding-3-large')
  index_name = 'tax-index'
  database = PineconeVectorStore.from_existing_index(index_name=index_name, 
                                                     embedding=embedding)

  llm = ChatOpenAI(model='gpt-4o')
  prompt = hub.pull("rlm/rag-prompt")
  retriever = database.as_retriever(search_kwargs={'k':4})

  qa_chain = RetrievalQA.from_chain_type(
      llm, 
      retriever=retriever,
      chain_type_kwargs={"prompt": prompt}
  )

  dictionary = ["사람을 나타내는 표현 -> 거주자"]

  prompt = ChatPromptTemplate.from_template(f"""
      사용자의 질문을 보고, 우리의 사전을 참고해서 사용자의 질문을 변경해주세요.
      만약 변경할 필요가 없다고 판단된다면, 사용자의 질문을 변경하지 않아도 됩니다.
      그런 경우에는 질문만 리턴해주세요
      사전: {dictionary}
      
      질문: {{question}}
  """)

  dictionary_chain = prompt | llm | StrOutputParser()
  tax_chain = {"query": dictionary_chain} | qa_chain
  ai_message = tax_chain.invoke({"question": user_message})
  
  return ai_message["result"]
      

if user_question := st.chat_input(placeholder="소득세에 관련된 궁금한 내용들을 말씀해 주세요.!"):
  with st.chat_message("user"):
    st.write(user_question)
  st.session_state.message_list.append({"role": "user", "content": user_question})
  
  with st.spinner("답변을 생성하는 중입니다."):
    ai_message = get_ai_message(user_question)
    with st.chat_message("ai"):  #  ====> 추가 부분분
      st.write(ai_message)
    st.session_state.message_list.append({"role": "ai", "content": ai_message})
  
 