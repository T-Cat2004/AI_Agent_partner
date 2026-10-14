import streamlit as st
import os
from datetime import datetime as dt #datetime为可以获取当前运行时间的模块
import json

from dotenv import load_dotenv
# 加载 .env 文件中的环境变量(streamlit 不会自动加载,如 DEEPSEEK_API_KEY)
load_dotenv()

#langchain相关导入
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

#设置页面的配置项
st.set_page_config(
    page_title="AI智能伴侣",
    page_icon="💕",
    #布局layout("centered","wide",or None)
    layout="wide",
    #控制侧边栏的状态
    initial_sidebar_state="expanded",
    #菜单的信息
    menu_items={}
)

#保存会话信息函数
def save_session():
    if st.session_state.current_session:
        session_data = {
            "system_name": st.session_state.system_name,
            "charater": st.session_state.charater,
            "current_session": st.session_state.current_session,
            "messages": st.session_state.messages
        }
        # 如果sessions目录不存在，则创建
        if not os.path.exists("sessions"):
            os.mkdir("sessions")

        # 保存会话数据
        with open(f"sessions/{st.session_state.current_session}.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

#加载所有的会话列表信息
def load_sessions():
    session_list = []
    #加载sessions目录下的所有会话信息
    if os.path.exists("sessions"):
       file_list=os.listdir("sessions")
       for filename in file_list:
           if filename.endswith(".json"):
               session_list.append(filename[:-5])
    session_list.sort(reverse=True) #排序，降序排列
    return session_list
#加载指定会话信息
def load_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            #读取会话数据

          with open(f"sessions/{session_name}.json","r",encoding="utf-8")as f:
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
            #如果删除的是当前会话，则需要更新消息列表
            if session_name==st.session_state.current_session:
                st.session_state.messages=[]
                st.session_state.current_session=dt.now().strftime("%Y-%m-%d_%H-%M-%S")
    except Exception:
        st.error("删除会话失败！")



#大标题
st.title("AI智能伴侣")

#添加logo
logo_path = r"D:\Python+Ai\Ai\resources\T Cat.jpg"
if os.path.exists(logo_path):
    st.logo(logo_path)

#系统提示词（系统人设）
system_prompt="""
    你是{nickname}，现在是用户的真实伴侣，请完全代入伴侣角色
    规则:
    1.每次只回一条消息
    2.静止任何场景或状态描述性文字
    3.要匹配用户使用的语言
    4.回复简短但注意重点
    5.为用户提供情绪价值，如果用户遇到什么难事，安慰或者鼓励用户
    6.有需要的话，可以用emoji表情表达情绪
    7.充分体现伴侣的性格特征
    性格特征：{character}
    请严格遵守上述规则与用户交流
"""

#初始化我们的聊天信息
# Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

#昵称
if "system_name" not in st.session_state:
    st.session_state.system_name = "绘梨衣"
#性格
if "charater" not in st.session_state:
    st.session_state.charater = "天真温柔专一热情的上海女孩"

#会话的标识（名字）
if "current_session" not in st.session_state:
    time=dt.now().strftime("%Y-%m-%d %H-%M-%S")
    st.session_state.current_session=time

st.text(f"会话名称:{st.session_state.current_session}")
#展示聊天信息
for message in st.session_state.messages:#{"role":"user","content":prompt}
    if message["role"]=="user":
        st.chat_message("user").write(message["content"])
    else:
        st.chat_message("assistant").write(message["content"])
#简化： st.chat_message(message["role"]).write(message["content"])


#1.创建与AI大模型交互的LLM对象（'DEEPSEEK_API_KEY'环境变量的名字，值就是DeepSeek的API_KEY的）
llm = ChatOpenAI(
    model="deepseek-v4-pro",
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com",
    reasoning_effort="high",
    extra_body={"thinking": {"type": "enabled"}},
)

#2.提示词模板:{nickname}昵称、{character}性格占位符，历史消息由MessagesPlaceholder自动注入
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder("history"),
])

#3.构建链式结构:prompt | llm | 输出解析器
chain = prompt | llm | StrOutputParser()

#左侧侧边栏--with:streamlit中的上下文管理器
# st.sidebar.subheader("伴侣的信息:")
# name=st.sidebar.text_input("昵称")
# info=st.sidebar.text_input("昵称") 不方便，不推荐

with st.sidebar:
    #会话信息
    st.subheader("AI控制面板")

    if st.button("新建会话",width="stretch",icon="🖊"):
        if st.session_state.messages:
        #1.保存当前会话
            save_session()
            #2.创建新的会话
            st.session_state.messages = []
            st.session_state.current_session=dt.now().strftime("%Y-%m-%d_%H-%M-%S")
            st.rerun()

    #会话历史
    st.text("会话历史")
    session_list=load_sessions()
    for session in session_list:
        col1,col2=st.columns([4,1])
        with col1:
            if st.button(session,width="stretch",icon="📄",type="primary" if session==st.session_state.current_session else "secondary"):
                #三元运算符:如果条件为真，则返回第一个表达式的值;否则,返回第二个表达式的值-->语法:值1 if 条件 else 表达式2
                load_session(session)
                st.rerun()
        with col2:
            if st.button("",width="stretch",icon="❌",key=f"delete_{session}"):
                delete_session(session)
                st.rerun()

#分隔线
    st.divider()

    st.subheader("伴侣的信息:")
    #昵称输入框
    system_name=st.text_input("昵称",placeholder="请输入昵称",value=st.session_state.system_name)#placeholder为输入框中的提示词，value为默认值
    if system_name:
        st.session_state.system_name=system_name

    #性格输入框
    charater=st.text_area("性格",placeholder="请输入性格",value=st.session_state.charater) #st.text.area():文本域
    if charater:
        st.session_state.charater=charater

#创建对话框(消息输入框)
user_input = st.chat_input("说点什么吧~")
if user_input: #字符串会自动转化为布尔值，如果字符串非空，则为True;否则为False
    st.chat_message("user").write(user_input)
    print("--------------->调用AI大模型，提示词为:",user_input)
    #保存用户输入的提示词到会话中
    st.session_state.messages.append({"role": "user", "content": user_input})


#调用链(非流式写法:full_response=chain.invoke({...}))
    #链会自动完成:组装提示词→调用大模型→解析输出
    response_message=st.empty()#创造一个空的组件，用于显示大模型返回的结果（在同一个位置更新进度文本，而不是生成5行不同的文本）
    full_response=""
    for chunk in chain.stream({
        "nickname": st.session_state.system_name,
        "character": st.session_state.charater,
        "history": st.session_state.messages, #对话历史由MessagesPlaceholder自动注入
    }):
        full_response+=chunk
        response_message.chat_message("assistant").write(full_response)

#保存AI大模型返回的结果到会话中
    st.session_state.messages.append({"role":"assistant", "content":full_response})

    #保存会话信息
    save_session()

