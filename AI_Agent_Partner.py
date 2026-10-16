import streamlit as st
import os
from datetime import datetime as dt, timedelta
import json
from langchain.chat_models import init_chat_model
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from dotenv import load_dotenv

load_dotenv()

# 1.页面配置
st.set_page_config(
    page_title="AI个人旅行助手",
    page_icon=r"D:\LangChain_study\heima_base\resource\VmrQkGdhg1.jpg",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)

# 2.logo
logo_path = r"D:\LangChain_study\heima_base\resource\VmrQkGdhg1.jpg"

# 3.RAG:构建向量库与检索
#构建向量库(缓存:整个应用只构建一次)
@st.cache_resource(show_spinner="正在加载旅行知识库...")
def get_vector_store():
    list_rag = ""
    for filename in os.listdir("travel_base"):
        with open(f"travel_base/{filename}", "r", encoding="utf-8") as f:
            text = f.read()
            list_rag += text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,
        chunk_overlap=30,
        length_function=len
    )
    text_docs = text_splitter.split_text(list_rag)
    vector_store = InMemoryVectorStore(embedding=DashScopeEmbeddings(model="text-embedding-v4"))
    vector_store.add_texts(text_docs)
    return vector_store

#RAG检索函数
def Rag_func(query: str):
    vector_store = get_vector_store()
    docs = vector_store.similarity_search(query, k=2)
    return "\n".join([doc.page_content for doc in docs])

# 4.工具定义
@tool
def get_weather(city:str):
    """获取主要想去的旅行城市的天气查询
    Args:
        city:城市的名称
    """
    weather_db = {
        "南京": "多云，温度26℃，空气良48%",
        "成都": "阴天，温度22℃，空气良55%",
        "西安": "晴天，温度24℃，空气良52%",
        "北京": "晴天，温度25℃，空气良40%",
        "重庆": "小雨，温度21℃，空气良58%",
        "洛阳": "多云，温度23℃，空气良50%",
        "武汉": "阴天，温度18℃，空气65%",
        "广州": "雷阵雨，温度17℃，空气60%",
        "长沙": "多云，温度25℃，空气良53%",
        "上海": "阴天，温度18℃，空气53%",
        "哈尔滨": "晴天，温度12℃，空气优35%",
        "阿坝州": "多云，温度10℃，空气优28%",
        "上饶": "小雨，温度20℃，空气优42%",
        "开封": "晴天，温度23℃，空气良56%",
        "黄山": "多云，温度15℃，空气优30%",
        "泰安": "晴天，温度21℃，空气良47%",
        "苏州": "阴天，温度18℃，空气60%",
        "中卫": "晴天，温度19℃，空气优33%",
    }
    result = weather_db.get(city)
    if result:
        return f"{city}:{result}"
    else:
        return f"{city}天气信息暂无"

@tool
def get_time(query_type:str = "current"):
    """
    获取时间相关的信息
    Args:
        query_type: 查询类型，默认为current
        "current": 获取当前时间
        "date": 获取今天的日期
        "tomorrow": 明天的日期
        "yesterday":昨天的日期
        "weekday": 获取今天是周几
    Returns:
        返回的是时间信息字符串
    """
    now = dt.now()
    if query_type=="current":
        return now.strftime("当前时间是：%Y年%m月%d日 %H-%M-%S")
    elif query_type == "date":
        return now.strftime("今天日期是：%Y年%m月%d日")
    elif query_type == "tomorrow":
        return (now + timedelta(days=1)).strftime("明天日期是：%Y年%m月%d日")
    elif query_type == "yesterday":
        return (now - timedelta(days=1)).strftime("昨天日期是：%Y年%m月%d日")
    elif query_type == "weekday":
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        return weekdays[now.weekday()]
    else:
        return "输入的查询类型有误"

@tool
def get_Rag(query:str):
    """当用户询问旅行注意事项时，使用Rag_func函数查询知识库并返回结果"""
    return Rag_func(query)



# 5.会话管理
#保存会话信息函数
def save_session():
    if st.session_state.current_session:
        session_data = {
            "system_name": st.session_state.system_name,
            "charater": st.session_state.charater,
            "current_session": st.session_state.current_session,
            "messages": st.session_state.messages
        }
        if not os.path.exists("sessions"):
            os.mkdir("sessions")
        with open(f"sessions/{st.session_state.current_session}.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

#加载所有的会话列表信息
def load_sessions():
    session_list = []
    if os.path.exists("sessions"):
       file_list=os.listdir("sessions")
       for filename in file_list:
           if filename.endswith(".json"):
               session_list.append(filename[:-5])
    session_list.sort(reverse=True)
    return session_list

#加载指定会话信息
def load_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            with open(f"sessions/{session_name}.json", "r", encoding="utf-8") as f:
                session_data=json.load(f)
                st.session_state.messages = session_data["messages"]
                st.session_state.system_name = session_data["system_name"]
                st.session_state.charater = session_data["charater"]
                st.session_state.current_session = session_name
    except Exception:
        st.error("加载会话失败！")

#删除会话信息函数
def delete_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            os.remove(f"sessions/{session_name}.json")
            if session_name==st.session_state.current_session:
                st.session_state.messages=[]
                st.session_state.current_session=dt.now().strftime("%Y-%m-%d_%H-%M-%S")
    except Exception:
        st.error("删除会话失败！")

# 6.大模型与智能体
llm = init_chat_model(
    model_provider="deepseek",
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY")
)

#定义智能体(缓存:昵称和性格不变时复用)
@st.cache_resource(show_spinner="正在初始化AI助手...")
def get_agent(nickname: str, character: str):
    return create_agent(
        model=llm,
        tools=[get_weather, get_time, get_Rag],
        system_prompt=f"""
             你是{nickname}，助理，知识库主要旅行注意事项，热门城市和热门景点等问题。
             你的性格{character}
             你可以使用下面的工具：
                 get_weather：查询想要旅游的城市天气
                 get_time：查询时间
                 get_Rag：查询旅行注意事项相关知识库
              回答的规则：
                 1.必须在有限的参考资料中回答，不要随意更改。
                 2.如果知识库中没有明确的答案，请说明“知识库中没有明确的记录”，再给出相关的建议
                 3.回复简洁专业，言简意赅，适合普通人群阅读
         """
    )

# 7.会话状态初始化
if "messages" not in st.session_state:
    st.session_state.messages = []

if "system_name" not in st.session_state:
    st.session_state.system_name = "小智"

if "charater" not in st.session_state:
    st.session_state.charater = "个人旅行助手"

if "current_session" not in st.session_state:
    time=dt.now().strftime("%Y-%m-%d %H-%M-%S")
    st.session_state.current_session=time

# 8.主界面
st.title("AI个人旅行系统🚅")
st.write("欢迎使用AI旅行问答系统")

if os.path.exists(logo_path):
    st.logo(logo_path)

st.text(f"会话名称:{st.session_state.current_session}")

for message in st.session_state.messages:
    if message["role"]=="user":
        st.chat_message("user").write(message["content"])
    else:
        st.chat_message("assistant").write(message["content"])

# 9.侧边栏
with st.sidebar:
    st.subheader("AI控制面板")

    if st.button("新建会话",width="stretch",icon="🖊"):
        if st.session_state.messages:
            save_session()
            st.session_state.messages = []
            st.session_state.current_session=dt.now().strftime("%Y-%m-%d_%H-%M-%S")
            st.rerun()

    st.text("会话历史")
    session_list=load_sessions()
    for session in session_list:
        col1,col2=st.columns([4,1])
        with col1:
            if st.button(session,width="stretch",icon="📄",type="primary" if session==st.session_state.current_session else "secondary"):
                load_session(session)
                st.rerun()
        with col2:
            if st.button("",width="stretch",icon="❌",key=f"delete_{session}"):
                delete_session(session)
                st.rerun()

    st.divider()

    st.subheader("旅行助手的信息:")
    system_name=st.text_input("昵称",placeholder="请输入昵称",value=st.session_state.system_name)
    if system_name:
        st.session_state.system_name=system_name

    charater=st.text_area("身份",placeholder="请输入身份设定",value=st.session_state.charater)
    if charater:
        st.session_state.charater=charater

# 10.聊天交互
user_input = st.chat_input("说点什么吧~")
if user_input:
    st.chat_message("user").write(user_input)
    print("--------------->调用AI大模型，提示词为:",user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    agent = get_agent(st.session_state.system_name, st.session_state.charater)

    response_message = st.empty()
    full_response = ""
    for message_chunk, _ in agent.stream(
        {"messages": st.session_state.messages},
        stream_mode="messages"
    ):
        if isinstance(message_chunk, AIMessage) and message_chunk.content:
            full_response += message_chunk.content
            response_message.chat_message("assistant").write(full_response)

    if full_response:
        st.session_state.messages.append({"role":"assistant", "content":full_response})

    save_session()
