import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface Conversation {
  thread_id: string
  title: string
  created_at: string
}

function App(): React.JSX.Element {
  // ===== 状态管理 =====
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [username, setUsername] = useState('')
  const [clientId, setClientId] = useState('')
  
  const [loginUsername, setLoginUsername] = useState('ljy')
  const [loginPassword, setLoginPassword] = useState('123456')
  const [loginApiKey, setLoginApiKey] = useState('sk-ac0005199de54aafbaf6a13ce1f788b5')
  const [loginError, setLoginError] = useState('')
  
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentThreadId, setCurrentThreadId] = useState('001')
  
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // ===== 删除弹窗状态 =====
  const [deleteDialog, setDeleteDialog] = useState<{
    show: boolean
    threadId: string
    title: string
  }>({
    show: false,
    threadId: '',
    title: ''
  })

  // ===== 自动滚动 =====
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // ===== 登录功能 =====
  const handleLogin = async () => {
    if (!loginUsername.trim()) {
      setLoginError('请输入用户名')
      return
    }

    try {
      const response = await fetch('http://localhost:8000/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: loginUsername,
          password: loginPassword,
          api_key: loginApiKey,
        }),
      })

      const data = await response.json()
      if (data.success) {
        setIsLoggedIn(true)
        setUsername(data.username)
        setClientId(data.client_id)
        setLoginError('')
        setMessages([])
        setCurrentThreadId('')
        
        loadConversations(data.client_id)
      } else {
        setLoginError('登录失败')
      }
    } catch (error) {
      setLoginError('连接后端失败')
    }
  }

  // ===== 加载对话历史列表 =====
  const loadConversations = async (cid: string) => {
    try {
      const response = await fetch(`http://localhost:8000/conversations/${cid}`)
      const data = await response.json()
      setConversations(data.conversations || [])
    } catch (error) {
      console.error('加载对话历史失败:', error)
    }
  }

  // ===== 加载指定会话的历史消息 =====
  const loadConversationHistory = async (cid: string, tid: string) => {
    try {
      const response = await fetch(`http://localhost:8000/history/${cid}/${tid}`)
      const data = await response.json()
      setMessages(data.messages || [])
    } catch (error) {
      console.error('加载会话历史失败:', error)
      setMessages([])
    }
  }

  // ===== 切换会话 =====
  const handleSelectConversation = (tid: string) => {
    setCurrentThreadId(tid)
    loadConversationHistory(clientId, tid)
  }

  // ===== 删除会话 =====
  const handleDeleteConversation = (tid: string, title: string) => {
    if (tid === currentThreadId) {
      return
    }
    setDeleteDialog({
      show: true,
      threadId: tid,
      title: title
    })
  }

  // ===== 确认删除 =====
  const confirmDelete = async () => {
    const tid = deleteDialog.threadId
    setDeleteDialog({ show: false, threadId: '', title: '' })

    try {
      const response = await fetch(`http://localhost:8000/conversations/${clientId}/${tid}`, {
        method: 'DELETE',
      })
      const data = await response.json()
      if (data.success) {
        loadConversations(clientId)
      }
    } catch (error) {
      console.error('删除对话失败:', error)
    }
  }

  // ===== 新建对话 =====
  const handleNewConversation = async () => {
    try {
      const response = await fetch(`http://localhost:8000/conversations/${clientId}`, {
        method: 'POST',
      })
      const data = await response.json()
      if (data.success) {
        setCurrentThreadId(data.thread_id)
        setMessages([])
        loadConversations(clientId)
      }
    } catch (error) {
      console.error('创建对话失败:', error)
    }
  }

  // ===== 发送消息（流式） =====
  const sendMessage = async () => {
    if (!input.trim()) return

    // 如果没有选中的会话，先创建一个新会话
    let threadId = currentThreadId
    if (!threadId) {
      try {
        const response = await fetch(`http://localhost:8000/conversations/${clientId}`, {
          method: 'POST',
        })
        const data = await response.json()
        if (data.success) {
          threadId = data.thread_id
          setCurrentThreadId(threadId)
          loadConversations(clientId)
        }
      } catch (error) {
        console.error('创建会话失败:', error)
        return
      }
    }

    const userMessage: Message = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    setMessages(prev => [...prev, { role: 'assistant', content: '' }])

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          client_id: clientId,
          thread_id: threadId,
        }),
      })

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No reader')

      const decoder = new TextDecoder()
      let accumulatedContent = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.content) {
                accumulatedContent = data.content
                setMessages(prev => {
                  const newMessages = [...prev]
                  newMessages[newMessages.length - 1] = {
                    role: 'assistant',
                    content: accumulatedContent,
                  }
                  return newMessages
                })
              }
            } catch (e) {
              // 忽略解析错误
            }
          }
        }
      }
      
      loadConversations(clientId)
    } catch (error) {
      console.error('Error:', error)
      setMessages(prev => {
        const newMessages = [...prev]
        newMessages[newMessages.length - 1] = {
          role: 'assistant',
          content: '抱歉，连接后端失败了。',
        }
        return newMessages
      })
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // ===== 登录页面 =====
  if (!isLoggedIn) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        backgroundColor: '#1a1a1a',
      }}>
        <div style={{
          padding: '40px',
          backgroundColor: '#272727',
          borderRadius: '12px',
          boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
          width: '360px',
          border: '1px solid #3a3a3a',
        }}>
          <h2 style={{
            textAlign: 'center',
            marginBottom: '30px',
            color: '#e9e9e9',
          }}>
            MyAgent 登录
          </h2>
          
          <div style={{ marginBottom: '20px' }}>
            <input
              type="text"
              value={loginUsername}
              onChange={(e) => setLoginUsername(e.target.value)}
              placeholder="用户名"
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid #3a3a3a',
                borderRadius: '8px',
                fontSize: '14px',
                outline: 'none',
                backgroundColor: '#1a1a1a',
                color: '#ffffff',
              }}
            />
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <input
              type="password"
              value={loginPassword}
              onChange={(e) => setLoginPassword(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
              placeholder="密码"
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid #3a3a3a',
                borderRadius: '8px',
                fontSize: '14px',
                outline: 'none',
                backgroundColor: '#1a1a1a',
                color: '#ffffff',
              }}
            />
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <input
              type="password"
              value={loginApiKey}
              onChange={(e) => setLoginApiKey(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
              placeholder="DeepSeek API Key"
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid #3a3a3a',
                borderRadius: '8px',
                fontSize: '14px',
                outline: 'none',
                backgroundColor: '#1a1a1a',
                color: '#ffffff',
              }}
            />
          </div>
          
          {loginError && (
            <div style={{
              color: '#ff6b6b',
              fontSize: '14px',
              marginBottom: '15px',
              textAlign: 'center',
            }}>
              {loginError}
            </div>
          )}
          
          <button
            onClick={handleLogin}
            style={{
              width: '100%',
              padding: '12px',
              backgroundColor: '#3a3a3a',
              color: '#e9e9e9',
              border: 'none',
              borderRadius: '8px',
              fontSize: '16px',
              cursor: 'pointer',
            }}
          >
            登录
          </button>
        </div>
      </div>
    )
  }

  // ===== 主界面（聊天 + 左侧历史） =====
  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      backgroundColor: '#1a1a1a',
    }}>
      {/* 左侧会话历史 */}
      <div style={{
        width: '260px',
        backgroundColor: '#272727',
        color: '#e9e9e9',
        display: 'flex',
        flexDirection: 'column',
      }}>
        {/* 用户信息 */}
        <div style={{
          padding: '16px',
          borderBottom: '1px solid #3a3a3a',
        }}>
          <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#e9e9e9' }}>{username}</div>
          <div style={{ fontSize: '12px', color: '#888888' }}>{clientId}</div>
        </div>
        
        {/* 新建对话按钮 */}
        <div style={{ padding: '12px' }}>
          <button 
            onClick={handleNewConversation}
            style={{
              width: '100%',
              padding: '10px',
              backgroundColor: '#3a3a3a',
              color: '#e9e9e9',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
            }}>
            + 新对话
          </button>
        </div>
        
        {/* 对话列表 */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '0 12px',
        }}>
          {conversations.length === 0 ? (
            <div style={{
              color: '#888888',
              fontSize: '14px',
              textAlign: 'center',
              marginTop: '20px',
            }}>
              暂无对话历史
            </div>
          ) : (
            conversations.map((conv, index) => (
              <div
                key={index}
                className="conversation-item"
                style={{
                  padding: '10px',
                  marginBottom: '8px',
                  backgroundColor: currentThreadId === conv.thread_id ? '#3a3a3a' : 'transparent',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
                onClick={() => handleSelectConversation(conv.thread_id)}
              >
                <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {conv.title}
                </span>
                {currentThreadId !== conv.thread_id && (
                  <span
                    style={{
                      marginLeft: '8px',
                      color: '#ff6b6b',
                      cursor: 'pointer',
                      fontSize: '14px',
                    }}
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDeleteConversation(conv.thread_id, conv.title)
                    }}
                  >
                    🗑️
                  </span>
                )}
              </div>
            ))
          )}
        </div>
        
        {/* 设置按钮 */}
        <div style={{
          padding: '16px',
          borderTop: '1px solid #3a3a3a',
          display: 'flex',
          alignItems: 'center',
        }}>
          <button style={{
            width: '100%',
            padding: '10px 14px',
            backgroundColor: '#3a3a3a',
            color: '#e9e9e9',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '14px',
          }}>
            ⚙️ 设置
          </button>
        </div>
      </div>
      
      {/* 右侧聊天区域 */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
      }}>
        {/* 头部 */}
        <div style={{
          padding: '16px',
          backgroundColor: '#272727',
          borderBottom: '1px solid #3a3a3a',
          fontSize: '18px',
          fontWeight: 'bold',
          color: '#e9e9e9',
        }}>
          MyAgent 智能助手
        </div>
        
        {/* 消息列表 */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '20px',
          backgroundColor: '#1a1a1a',
        }}>
          {messages.length === 0 && (
            <div style={{
              textAlign: 'center',
              color: '#888888',
              marginTop: '50px',
            }}>
              你好！我是你的 AI 助手，有什么可以帮你的吗？
            </div>
          )}
          {messages.map((msg, index) => (
            <div
              key={index}
              style={{
                display: 'flex',
                justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                marginBottom: '12px',
              }}
            >
              <div style={{
                maxWidth: '70%',
                padding: '10px 14px',
                borderRadius: '12px',
                backgroundColor: msg.role === 'user' ? '#3a3a3a' : '#272727',
                color: '#e9e9e9',
                lineHeight: '1.5',
                boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
              }}>
                {msg.role === 'assistant' ? (
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                ) : (
                  msg.content
                )}
              </div>
            </div>
          ))}
          {loading && messages[messages.length - 1]?.content === '' && (
            <div style={{
              textAlign: 'center',
              color: '#888888',
              padding: '10px',
            }}>
              正在输入...
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        
        {/* 输入框 */}
        <div style={{
          padding: '16px',
          backgroundColor: '#272727',
          borderTop: '1px solid #3a3a3a',
        }}>
          <div style={{
            display: 'flex',
            gap: '10px',
          }}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入消息..."
              style={{
                flex: 1,
                padding: '10px 14px',
                border: '1px solid #3a3a3a',
                borderRadius: '8px',
                fontSize: '14px',
                outline: 'none',
                backgroundColor: '#232528',
                color: '#e9e9e9',
              }}
            />
            <button
              onClick={sendMessage}
              disabled={loading}
              style={{
                padding: '10px 20px',
                backgroundColor: '#3a3a3a',
                color: '#e9e9e9',
                border: 'none',
                borderRadius: '8px',
                fontSize: '14px',
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.6 : 1,
              }}
            >
              发送
            </button>
          </div>
        </div>
      </div>

      {/* 删除确认弹窗 */}
      {deleteDialog.show && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.6)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000,
        }}>
          <div style={{
            backgroundColor: '#272727',
            borderRadius: '12px',
            padding: '28px',
            width: '360px',
            border: '1px solid #3a3a3a',
            boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
          }}>
            <div style={{
              fontSize: '18px',
              fontWeight: 'bold',
              color: '#e9e9e9',
              marginBottom: '16px',
            }}>
              删除对话
            </div>
            <div style={{
              fontSize: '14px',
              color: '#888888',
              marginBottom: '24px',
              lineHeight: '1.5',
            }}>
              确定要删除「{deleteDialog.title}」吗？此操作无法撤销。
            </div>
            <div style={{
              display: 'flex',
              gap: '12px',
              justifyContent: 'flex-end',
            }}>
              <button
                onClick={() => setDeleteDialog({ show: false, threadId: '', title: '' })}
                style={{
                  padding: '10px 20px',
                  backgroundColor: 'transparent',
                  color: '#e9e9e9',
                  border: '1px solid #3a3a3a',
                  borderRadius: '8px',
                  fontSize: '14px',
                  cursor: 'pointer',
                }}
              >
                取消
              </button>
              <button
                onClick={confirmDelete}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#ff4d4f',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '14px',
                  cursor: 'pointer',
                }}
              >
                删除
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
