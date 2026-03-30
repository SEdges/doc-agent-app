"""
Joern Docs Web Agent
构建网页文档知识库 + 启动网页问答界面
"""

import os
import streamlit as st
import requests
from bs4 import BeautifulSoup
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


# =============================
# 配置与环境变量检查
# =============================
def check_openai_key():
    """检查并获取 OpenAI API Key"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("❌ 未找到 OPENAI_API_KEY 环境变量！")
        st.info(
            """
            请设置环境变量后重启应用：
            
            **Windows PowerShell:**
            ```
            $env:OPENAI_API_KEY="sk-proj-xxxxx"
            streamlit run joern_doc_agent_app.py
            ```
            
            **Linux/Mac:**
            ```
            export OPENAI_API_KEY='sk-proj-xxxxx'
            streamlit run joern_doc_agent_app.py
            ```
            """
        )
        st.stop()
    return api_key


# =============================
# 抓取 Joern 文档链接
# =============================
@st.cache_data(show_spinner=False)
def crawl_joern_docs(base_url="https://docs.joern.io"):
    """
    递归抓取 Joern 文档的所有页面链接
    
    策略：
    1. 从首页开始，提取所有文档链接
    2. 递归访问每个链接，继续提取新链接
    3. 去重并返回所有唯一的文档页面
    """
    visited = set()
    to_visit = {base_url}
    all_links = set()
    
    # 限制抓取深度，避免无限递归
    max_pages = 100
    count = 0
    
    while to_visit and count < max_pages:
        current_url = to_visit.pop()
        
        # 跳过已访问的页面
        if current_url in visited:
            continue
        
        visited.add(current_url)
        count += 1
        
        try:
            resp = requests.get(current_url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # 提取所有链接
            for a in soup.find_all("a", href=True):
                href = a["href"]
                
                # 处理相对路径
                if href.startswith("/"):
                    full_url = base_url.rstrip("/") + href
                elif href.startswith(base_url):
                    full_url = href
                else:
                    continue
                
                # 移除 URL 片段（#anchor）
                full_url = full_url.split("#")[0]
                
                # 只保留 docs.joern.io 的页面，排除外部链接
                if full_url.startswith(base_url) and full_url not in visited:
                    all_links.add(full_url)
                    to_visit.add(full_url)
        
        except Exception as e:
            print(f"Error crawling {current_url}: {e}")
            continue
    
    # 确保包含首页
    all_links.add(base_url)
    
    return sorted(list(all_links))


# =============================
# 加载网页内容
# =============================
@st.cache_resource(show_spinner=True)
def load_docs(urls):
    """
    使用 WebBaseLoader 加载静态 HTML 文档
    注意：Playwright 在 Windows + Streamlit 环境下有兼容性问题
    对于 Joern 文档这种静态网站，WebBaseLoader 完全够用
    """
    # 设置 User-Agent 避免被某些网站拦截
    if not os.getenv("USER_AGENT"):
        os.environ["USER_AGENT"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    loader = WebBaseLoader(urls)
    return loader.load()


# =============================
# 构建向量数据库
# =============================
@st.cache_resource(show_spinner=True)
def build_vector_db(documents, api_key):
    """构建向量数据库，显式使用指定的 API Key"""
    splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=100)
    chunks = splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings(openai_api_key=api_key)
    # Chroma 0.4+ 自动持久化，无需调用 persist()
    db = Chroma.from_documents(chunks, embeddings, persist_directory="./joern_docs_db")
    return db


# =============================
# 创建问答Agent（支持多轮对话）
# =============================
def create_conversational_agent(db, api_key):
    """
    创建支持多轮对话的 Agent
    
    Args:
        db: 向量数据库
        api_key: OpenAI API Key
    
    Returns:
        函数：接受 (query, chat_history) 返回答案
    """
    retriever = db.as_retriever(search_kwargs={"k": 3})
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0, openai_api_key=api_key)
    
    def format_docs(docs):
        """格式化检索到的文档"""
        return "\n\n".join(doc.page_content for doc in docs)
    
    def format_chat_history(history):
        """格式化对话历史"""
        if not history:
            return "（无历史对话）"
        
        formatted = []
        for msg in history:
            role = "用户" if msg["role"] == "user" else "助手"
            formatted.append(f"{role}: {msg['content']}")
        return "\n".join(formatted)
    
    def answer_with_context(query, chat_history=None):
        """
        基于检索到的文档和对话历史回答问题
        
        Args:
            query: 用户当前问题
            chat_history: 对话历史列表 [{"role": "user/assistant", "content": "..."}]
        
        Returns:
            答案字符串
        """
        if chat_history is None:
            chat_history = []
        
        # 检索相关文档
        docs = retriever.invoke(query)
        context = format_docs(docs)
        history_text = format_chat_history(chat_history)
        
        # 构建包含历史的 prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", 
             "你是一个专业的 Joern 文档助手。你的任务是基于提供的文档上下文和对话历史，回答用户关于 Joern 的问题。\n\n"
             "请注意：\n"
             "1. 优先使用文档上下文中的信息\n"
             "2. 如果用户的问题涉及之前的对话，参考对话历史\n"
             "3. 如果文档中没有相关信息，诚实地告知用户\n"
             "4. 根据对话历史，猜测用户可能想要了解的内容，并询问用户是否需要进一步了解\n"
             "5. 用清晰、专业的语言回答\n\n"
             "=== 相关文档 ===\n{context}\n\n"
             "=== 对话历史 ===\n{history}"),
            ("user", "{question}")
        ])
        
        # 生成回答
        chain = prompt | llm | StrOutputParser()
        answer = chain.invoke({
            "context": context,
            "history": history_text,
            "question": query
        })
        
        return answer
    
    return answer_with_context


# =============================
# Streamlit UI
# =============================
def main():
    st.set_page_config(page_title="Joern Docs Agent", page_icon="🧩", layout="wide")
    
    # 检查 API Key（会自动从环境变量读取）
    api_key = check_openai_key()
    
    st.title("🧠 Joern Docs 知识问答 Agent")

    st.markdown(
        """
        这个 Agent 能理解 [docs.joern.io](https://docs.joern.io) 的所有说明文档。  
        你可以直接提问，例如：
        - Joern 的 Code Property Graph 是什么？
        - 如何运行 Joern CLI？
        - 支持哪些语言的解析？

        ---
        """
    )

    with st.sidebar:
        st.success(f"✅ 使用的 API Key (后4位): ...{api_key[-4:]}")
        st.caption(f"完整前缀: {api_key[:12]}...")
        
        # 调试信息：显示环境变量来源
        with st.expander("🔍 调试信息"):
            st.code(f"环境变量 OPENAI_API_KEY 后4位: {api_key[-4:]}")
            st.code(f"Key 前缀: {api_key[:20]}...")
        
        st.header("📦 构建知识库")
        
        # 显示当前知识库状态
        if "db_ready" in st.session_state:
            st.success("✅ 知识库已就绪")
            if st.button("🔄 重新构建知识库", use_container_width=True):
                # 清除缓存和状态
                st.cache_data.clear()
                st.cache_resource.clear()
                if "db_ready" in st.session_state:
                    del st.session_state["db_ready"]
                st.info("缓存已清除，请点击下方按钮重新构建")
                st.rerun()
        
        if st.button("🚀 开始抓取并构建", use_container_width=True):
            with st.spinner("正在递归抓取所有文档链接..."):
                urls = crawl_joern_docs()
                st.success(f"✅ 共发现 {len(urls)} 个文档页面")
                
                # 显示部分链接
                with st.expander("📋 查看抓取到的页面"):
                    for i, url in enumerate(urls[:20], 1):
                        st.text(f"{i}. {url}")
                    if len(urls) > 20:
                        st.text(f"... 还有 {len(urls) - 20} 个页面")

            with st.spinner("正在加载网页内容（可能需要几分钟）..."):
                docs = load_docs(urls)
                st.success(f"✅ 已加载 {len(docs)} 个网页")

            with st.spinner("正在构建向量数据库并生成嵌入..."):
                db = build_vector_db(docs, api_key)
                st.session_state["db_ready"] = True
                st.success("🎉 知识库构建完成！现在可以开始提问了")
                st.balloons()

    if "db_ready" not in st.session_state:
        st.info("请点击左侧按钮，先构建 Joern 文档知识库。")
        st.stop()

    # 初始化对话历史
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # 创建支持多轮对话的 Agent
    db = Chroma(
        persist_directory="./joern_docs_db", 
        embedding_function=OpenAIEmbeddings(openai_api_key=api_key)
    )
    agent = create_conversational_agent(db, api_key)

    # 侧边栏：对话控制
    with st.sidebar:
        st.header("💬 对话控制")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ 清空对话", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()
        with col2:
            if st.button("📊 查看统计", use_container_width=True):
                st.info(f"已进行 {len(st.session_state.chat_history)} 轮对话")
        
        # 示例问题
        st.subheader("💡 示例问题")
        example_questions = [
            "Joern 的 Code Property Graph 是什么？",
            "如何安装和运行 Joern？",
            "Joern 支持哪些编程语言？",
            "什么是 CPG 的节点和边？",
            "如何使用 Joern 进行代码分析？"
        ]
        for i, q in enumerate(example_questions):
            if st.button(f"📌 {q[:20]}...", key=f"example_{i}", use_container_width=True):
                # 将示例问题添加到输入框
                st.session_state.example_query = q

    # 显示对话历史
    st.subheader("📜 对话历史")
    
    if not st.session_state.chat_history:
        st.info("💡 开始提问吧！我会记住之前的对话内容，你可以进行多轮深入探讨。")
    else:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # 用户输入区域
    default_query = st.session_state.pop("example_query", "")
    query = st.chat_input("输入你的问题...", key="user_input") or default_query
    
    if query:
        # 显示用户问题
        with st.chat_message("user"):
            st.markdown(query)
        
        # 添加到历史
        st.session_state.chat_history.append({"role": "user", "content": query})
        
        # 生成回答
        with st.chat_message("assistant"):
            with st.spinner("正在思考..."):
                # 传递历史记录（不包括刚添加的用户问题）
                history_for_context = st.session_state.chat_history[:-1]
                answer = agent(query, history_for_context)
            st.markdown(answer)
        
        # 添加助手回答到历史
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        
        # 自动滚动到最新消息
        st.rerun()


if __name__ == "__main__":
    main()
