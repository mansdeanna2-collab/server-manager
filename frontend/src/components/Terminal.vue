<template>
  <div class="terminal-wrapper">
    <div
      ref="terminalRef"
      class="terminal-container"
    />
    <div
      v-if="!connected && !connecting"
      class="terminal-overlay"
    >
      <div class="overlay-content">
        <el-icon
          :size="48"
          class="terminal-icon"
        >
          <Monitor />
        </el-icon>
        <p>点击连接按钮开始</p>
        <el-button
          type="primary"
          size="large"
          @click="connect"
        >
          <el-icon><Connection /></el-icon>
          连接终端
        </el-button>
      </div>
    </div>
    <div
      v-if="connecting"
      class="terminal-overlay"
    >
      <div class="overlay-content">
        <el-icon
          :size="48"
          class="loading-icon"
        >
          <Loading />
        </el-icon>
        <p>正在连接...</p>
      </div>
    </div>
    <div
      v-if="error"
      class="terminal-overlay error-overlay"
    >
      <div class="overlay-content">
        <el-icon
          :size="48"
          class="error-icon"
        >
          <CircleClose />
        </el-icon>
        <p>{{ error }}</p>
        <el-button
          type="primary"
          size="large"
          @click="connect"
        >
          重新连接
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import { WebLinksAddon } from 'xterm-addon-web-links'
import { io } from 'socket.io-client'
import { Monitor, Connection, Loading, CircleClose } from '@element-plus/icons-vue'
import 'xterm/css/xterm.css'

const props = defineProps({
  server: {
    type: Object,
    required: true
  },
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['connected', 'disconnected', 'error'])

const terminalRef = ref(null)
const connected = ref(false)
const connecting = ref(false)
const error = ref('')

let terminal = null
let fitAddon = null
let socket = null
let resizeObserver = null

const initTerminal = () => {
  if (!terminalRef.value || terminal) return

  terminal = new Terminal({
    cursorBlink: true,
    cursorStyle: 'block',
    fontSize: 14,
    fontFamily: 'Monaco, Menlo, Consolas, monospace',
    theme: {
      background: '#1e1e1e',
      foreground: '#d4d4d4',
      cursor: '#ffffff',
      cursorAccent: '#1e1e1e',
      selection: 'rgba(255, 255, 255, 0.3)',
      black: '#000000',
      red: '#cd3131',
      green: '#0dbc79',
      yellow: '#e5e510',
      blue: '#2472c8',
      magenta: '#bc3fbc',
      cyan: '#11a8cd',
      white: '#e5e5e5',
      brightBlack: '#666666',
      brightRed: '#f14c4c',
      brightGreen: '#23d18b',
      brightYellow: '#f5f543',
      brightBlue: '#3b8eea',
      brightMagenta: '#d670d6',
      brightCyan: '#29b8db',
      brightWhite: '#ffffff'
    },
    scrollback: 1000,
    tabStopWidth: 4
  })

  fitAddon = new FitAddon()
  terminal.loadAddon(fitAddon)
  terminal.loadAddon(new WebLinksAddon())

  terminal.open(terminalRef.value)

  // 发送输入到服务器
  terminal.onData((data) => {
    if (socket && connected.value) {
      socket.emit('terminal_input', { data })
    }
  })

  // 监听终端大小变化
  resizeObserver = new ResizeObserver(() => {
    if (fitAddon && terminal) {
      try {
        fitAddon.fit()
        if (socket && connected.value) {
          socket.emit('terminal_resize', {
            cols: terminal.cols,
            rows: terminal.rows
          })
        }
      } catch (e) {
        // Resize errors are non-critical, log for debugging
        if (import.meta.env.DEV) {
          // eslint-disable-next-line no-console
          console.warn('Terminal resize error:', e)
        }
      }
    }
  })
  resizeObserver.observe(terminalRef.value)

  nextTick(() => {
    try {
      fitAddon.fit()
    } catch (e) {
      // Initial fit errors are non-critical
      if (import.meta.env.DEV) {
        // eslint-disable-next-line no-console
        console.warn('Terminal initial fit error:', e)
      }
    }
  })
}

const connect = () => {
  if (connecting.value || connected.value) return

  connecting.value = true
  error.value = ''

  const token = localStorage.getItem('token')
  if (!token) {
    error.value = '请先登录'
    connecting.value = false
    return
  }

  // 获取WebSocket URL
  // 优先使用 VITE_WS_URL 环境变量
  // 如果未设置，则从 VITE_API_BASE_URL 推断后端地址
  // 最后回退到 window.location.origin
  let wsUrl = import.meta.env.VITE_WS_URL
  if (!wsUrl) {
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL
    if (apiBaseUrl && apiBaseUrl.startsWith('http')) {
      // 从 API URL 中提取基础URL（去掉/api路径）
      try {
        const url = new URL(apiBaseUrl)
        wsUrl = url.origin
      } catch (_e) {
        wsUrl = window.location.origin
      }
    } else {
      wsUrl = window.location.origin
    }
  }

  socket = io(`${wsUrl}/terminal`, {
    transports: ['polling', 'websocket'],
    reconnection: true,
    reconnectionAttempts: 3,
    reconnectionDelay: 1000,
    timeout: 20000,
    upgrade: true
  })

  socket.on('connect', () => {
    // 发送启动终端请求
    socket.emit('start_terminal', {
      server_id: props.server.id,
      token: token
    })
  })

  socket.on('terminal_connected', (data) => {
    connecting.value = false
    connected.value = true
    error.value = ''
    terminal.writeln(`\r\n\x1b[32m${data.message}\x1b[0m\r\n`)
    emit('connected')

    // 发送终端大小
    if (terminal) {
      socket.emit('terminal_resize', {
        cols: terminal.cols,
        rows: terminal.rows
      })
    }
  })

  socket.on('terminal_output', (data) => {
    if (terminal && data.data) {
      terminal.write(data.data)
    }
  })

  socket.on('terminal_error', (data) => {
    connecting.value = false
    connected.value = false
    error.value = data.message || '连接失败'
    emit('error', error.value)
  })

  socket.on('terminal_disconnected', () => {
    connecting.value = false
    connected.value = false
    terminal.writeln('\r\n\x1b[31m连接已断开\x1b[0m')
    emit('disconnected')
  })

  socket.on('disconnect', () => {
    if (connected.value) {
      connected.value = false
      terminal.writeln('\r\n\x1b[31m连接已断开\x1b[0m')
      emit('disconnected')
    }
    connecting.value = false
  })

  socket.on('connect_error', () => {
    connecting.value = false
    error.value = '无法连接到服务器'
    emit('error', error.value)
  })
}

const disconnect = () => {
  if (socket) {
    socket.emit('stop_terminal')
    socket.disconnect()
    socket = null
  }
  connected.value = false
  connecting.value = false
}

// 监听visible变化，初始化终端
watch(() => props.visible, (newVal) => {
  if (newVal) {
    nextTick(() => {
      initTerminal()
    })
  }
})

onMounted(() => {
  if (props.visible) {
    nextTick(() => {
      initTerminal()
    })
  }
})

onUnmounted(() => {
  disconnect()
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
  if (terminal) {
    terminal.dispose()
    terminal = null
  }
})

// 暴露方法给父组件
defineExpose({
  connect,
  disconnect
})
</script>

<style scoped>
.terminal-wrapper {
  position: relative;
  width: 100%;
  height: 500px;
  background: #1e1e1e;
  border-radius: 8px;
  overflow: hidden;
}

.terminal-container {
  width: 100%;
  height: 100%;
  padding: 10px;
  box-sizing: border-box;
}

.terminal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(30, 30, 30, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
}

.error-overlay {
  background: rgba(30, 30, 30, 0.98);
}

.overlay-content {
  text-align: center;
  color: #d4d4d4;
}

.overlay-content p {
  margin: 16px 0;
  font-size: 16px;
}

.terminal-icon {
  color: #67c23a;
}

.loading-icon {
  color: #409EFF;
  animation: spin 1s linear infinite;
}

.error-icon {
  color: #f56c6c;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* xterm样式覆盖 */
:deep(.xterm) {
  padding: 0;
}

:deep(.xterm-viewport) {
  overflow-y: auto !important;
}
</style>
