# 贡献指南 🤝

感谢你考虑为 Joern Docs Agent 做出贡献！

---

## 🎯 贡献方式

### 报告 Bug

如果你发现了 Bug，请：

1. 检查 [现有 Issues](https://github.com/your-username/doc-agent-app/issues) 是否已有人报告
2. 如果没有，创建新 Issue，包含：
   - 📝 清晰的标题
   - 🔍 详细的复现步骤
   - 💻 你的环境信息（OS、Python 版本、依赖版本）
   - 📸 截图或错误日志（如果有）

### 提出新功能

1. 先在 Issues 中讨论你的想法
2. 等待维护者反馈
3. 获得批准后再开始开发

### 提交代码

1. **Fork** 本仓库
2. **创建分支**：`git checkout -b feature/amazing-feature`
3. **编写代码**（参考下方代码规范）
4. **提交更改**：`git commit -m 'Add amazing feature'`
5. **推送分支**：`git push origin feature/amazing-feature`
6. **创建 Pull Request**

---

## 📝 代码规范

### Python 风格

遵循 [PEP 8](https://pep8.org/) 和 [Zen of Python](https://www.python.org/dev/peps/pep-0020/)：

```python
# ✅ 好的代码
def calculate_similarity(doc1, doc2):
    """计算两个文档的相似度"""
    return cosine_similarity(doc1, doc2)

# ❌ 不好的代码
def calc_sim(d1,d2): return cosine_similarity(d1,d2)
```

### 命名规范

- **函数/变量**：`snake_case`
- **类**：`PascalCase`
- **常量**：`UPPER_SNAKE_CASE`
- **私有**：`_leading_underscore`

```python
# 函数
def load_documents(urls):
    pass

# 类
class DocumentLoader:
    pass

# 常量
MAX_RETRY_COUNT = 3

# 私有
def _internal_helper():
    pass
```

### 注释规范

使用中文注释，清晰说明**为什么**而不仅仅是**做什么**：

```python
# ✅ 好的注释
# 使用递归抓取确保获取所有子页面，避免遗漏深层文档
def crawl_docs(base_url):
    pass

# ❌ 不好的注释
# 抓取文档
def crawl_docs(base_url):
    pass
```

### Docstring 规范

```python
def create_agent(db, api_key):
    """
    创建支持多轮对话的 Agent
    
    Args:
        db: 向量数据库实例
        api_key: OpenAI API Key
    
    Returns:
        函数：接受 (query, history) 返回答案字符串
    
    Raises:
        ValueError: 如果 API Key 无效
    """
    pass
```

---

## 🧪 测试

### 运行测试前

```bash
# 激活环境
conda activate joern-docs

# 确保依赖最新
pip install -r requirements.txt
```

### 手动测试清单

提交 PR 前，请确保：

- ✅ 应用能正常启动
- ✅ 知识库能成功构建
- ✅ 能正确回答示例问题
- ✅ 多轮对话功能正常
- ✅ 清空对话功能正常
- ✅ 无明显的 UI 错误

### 测试用例示例

```python
# 测试文档抓取
urls = crawl_joern_docs()
assert len(urls) >= 30, "应至少抓取 30 个页面"
assert "https://docs.joern.io" in urls, "应包含首页"

# 测试 Agent 回答
answer = agent("Joern 是什么？", [])
assert "代码分析" in answer or "Code Property Graph" in answer
```

---

## 📋 提交信息规范

使用清晰的提交信息：

### 格式

```
<类型>: <简短描述>

<详细描述（可选）>

<相关 Issue（可选）>
```

### 类型

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构（不是新功能也不是修 Bug）
- `perf`: 性能优化
- `test`: 添加测试
- `chore`: 构建过程或辅助工具的变动

### 示例

```
feat: 添加导出对话历史功能

允许用户将对话记录导出为 Markdown 文件

Closes #42
```

---

## 🔍 代码审查

### PR 检查清单

提交 PR 时，请确保：

- ✅ 代码遵循项目风格
- ✅ 添加了必要的注释和 docstring
- ✅ 没有引入明显的性能问题
- ✅ 没有硬编码的密钥或敏感信息
- ✅ 更新了相关文档（如果需要）

### 审查标准

**好的 PR**：
- 🟢 职责单一（一个 PR 只做一件事）
- 🟢 改动合理（不过度设计）
- 🟢 代码清晰（易于理解和维护）
- 🟢 有必要的注释

**需要改进的 PR**：
- 🔴 混合多个不相关的改动
- 🔴 过度复杂的实现
- 🔴 缺少注释或文档
- 🔴 引入不必要的依赖

---

## 💡 设计原则

本项目遵循以下原则（参考 Linus Torvalds 和 Zen of Python）：

### 1. 简单胜于复杂

```python
# ✅ 简单直接
def format_history(history):
    return "\n".join(f"{msg['role']}: {msg['content']}" for msg in history)

# ❌ 过度设计
class HistoryFormatter:
    def __init__(self, strategy="default"):
        self.strategy = strategy
    
    def format(self, history):
        if self.strategy == "default":
            # ... 复杂逻辑
```

### 2. 显式胜于隐式

```python
# ✅ 显式传递参数
def create_agent(db, api_key):
    llm = ChatOpenAI(openai_api_key=api_key)

# ❌ 隐式依赖全局变量
def create_agent(db):
    llm = ChatOpenAI()  # 从哪里来的 API Key？
```

### 3. 实用主义战胜纯粹性

```python
# ✅ 实用：限制抓取数量，避免无限递归
max_pages = 100
while to_visit and count < max_pages:
    # ...

# ❌ 纯粹但不实用：可能导致无限循环
while to_visit:
    # ...
```

### 4. 消除特殊情况

```python
# ✅ 统一处理
def handle_url(url):
    # 所有 URL 都用同样的逻辑处理
    return normalize(url)

# ❌ 太多特殊情况
def handle_url(url):
    if url.startswith("http://"):
        # 特殊处理 1
    elif url.startswith("https://"):
        # 特殊处理 2
    elif url.startswith("/"):
        # 特殊处理 3
```

---

## 🙋 需要帮助？

- 💬 在 Issue 中提问
- 📧 联系维护者
- 📖 查看 [项目文档](README.md)

---

## 📜 行为准则

- ✅ 尊重所有贡献者
- ✅ 保持专业和友善
- ✅ 接受建设性的批评
- ✅ 关注技术问题，而非个人

---

**感谢你的贡献！** 🎉

