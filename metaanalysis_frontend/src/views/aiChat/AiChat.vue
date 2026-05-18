<template>
  <div>
    <div class="page-header">
      <h2>AI智能问答</h2>
    </div>

    <div class="chat-layout">
      <!-- 左侧：数据集选择 -->
      <div class="dataset-panel page-card">
        <h3>当前数据集</h3>
        <el-select v-model="currentDataset" style="width:100%;margin-bottom:12px" @change="onDatasetChange">
          <el-option v-for="ds in datasetList" :key="ds.id" :label="ds.name" :value="ds.id" />
        </el-select>
        <el-divider>字段说明</el-divider>
        <div class="field-list">
          <div v-for="f in fieldList" :key="f.name" class="field-item">
            <el-icon><Coin /></el-icon>
            <span :title="`${f.dtype} | 非空:${f.non_null} | 唯一值:${f.unique}`">{{ f.name }}</span>
          </div>
          <div v-if="fieldList.length === 0 && currentDataset" style="color:#909399;font-size:12px;text-align:center;padding:20px 0">
            加载中...
          </div>
        </div>
        <el-divider>快捷提问</el-divider>
        <div class="quick-actions">
          <el-button size="small" @click="quickAsk('数据概况')">📊 数据概览</el-button>
          <el-button size="small" @click="quickAsk('缺失值分析')">🔍 缺失值</el-button>
          <el-button size="small" @click="quickAsk('自动探索分析')">🚀 自动探索</el-button>
        </div>
      </div>

      <!-- 中间：对话区 -->
      <div class="chat-panel">
        <div class="chat-messages" ref="messagesRef">
          <div v-for="msg in messages" :key="msg.id" :class="['message', msg.role]">
            <div class="msg-avatar">{{ msg.role === 'user' ? '我' : 'AI' }}</div>
            <div class="msg-content">
              <p v-html="formatContent(msg.content)"></p>
            </div>
          </div>
          <div v-if="messages.length === 0" class="chat-placeholder">
            <el-icon :size="48" color="#c0c4cc"><ChatDotRound /></el-icon>
            <p>选择数据集后，用自然语言提问</p>
            <p style="font-size:12px;color:#909399">例如："分析各地区销售金额的分布情况"</p>
          </div>
        </div>
        <div class="chat-input">
          <el-input
            v-model="inputMsg"
            placeholder="输入你的分析问题..."
            @keyup.enter="sendMessage"
            size="large"
            :disabled="!currentDataset"
          >
            <template #append>
              <el-button type="primary" @click="sendMessage" :loading="sending">
                <el-icon><Promotion /></el-icon>
              </el-button>
            </template>
          </el-input>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { sendMessage as apiSendMessage, getFields as apiGetFields } from '@/api/aiChat'
import { getDatasets } from '@/api/dataset'

const currentDataset = ref(null)
const inputMsg = ref('')
const sending = ref(false)
const messagesRef = ref(null)
const datasetList = ref([])
const fieldList = ref([])
const messages = ref([])

onMounted(async () => {
  try {
    const res = await getDatasets()
    datasetList.value = res.data?.items || res.data || []
    if (datasetList.value.length > 0) {
      currentDataset.value = datasetList.value[0].id
      await onDatasetChange()
    }
  } catch (e) {
    console.error('加载数据集失败', e)
  }
})

async function onDatasetChange() {
  if (!currentDataset.value) return
  fieldList.value = []
  messages.value = []
  try {
    const res = await apiGetFields(currentDataset.value)
    fieldList.value = res.data?.fields || []
  } catch (e) {
    console.error('加载字段失败', e)
  }
}

async function sendMessage() {
  if (!inputMsg.value.trim() || !currentDataset.value) return
  const userMsg = { id: Date.now(), role: 'user', content: inputMsg.value }
  messages.value.push(userMsg)
  const question = inputMsg.value
  inputMsg.value = ''
  sending.value = true

  await nextTick()
  messagesRef.value.scrollTop = messagesRef.value.scrollHeight

  try {
    const res = await apiSendMessage({
      question,
      dataset_id: Number(currentDataset.value),
    })
    const reply = res.data?.reply || res.data?.content || '分析完成，未获取到结果'
    messages.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: reply,
    })
  } catch (e) {
    messages.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: `分析失败: ${e.message}`,
    })
  } finally {
    sending.value = false
    await nextTick()
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

async function quickAsk(question) {
  if (!currentDataset.value) {
    ElMessage.warning('请先选择数据集')
    return
  }
  inputMsg.value = question
  await sendMessage()
}

function formatContent(text) {
  if (!text) return ''
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
}
</script>

<style scoped>
.chat-layout { display: grid; grid-template-columns: 220px 1fr; gap: 16px; height: calc(100vh - 140px); }
.chat-panel {
  display: flex; flex-direction: column; background: #fff;
  border-radius: 8px; box-shadow: var(--shadow); overflow: hidden;
}
.chat-messages {
  flex: 1; overflow-y: auto; padding: 20px;
  display: flex; flex-direction: column; gap: 16px;
}
.message { display: flex; gap: 12px; max-width: 80%; }
.message.user { align-self: flex-end; flex-direction: row-reverse; }
.msg-avatar {
  width: 36px; height: 36px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 600; flex-shrink: 0;
}
.message.user .msg-avatar { background: var(--primary); color: #fff; }
.message.assistant .msg-avatar { background: #f0f9ff; color: var(--primary); }
.msg-content {
  padding: 12px 16px; border-radius: 8px; font-size: 14px; line-height: 1.6;
}
.message.user .msg-content { background: var(--primary); color: #fff; }
.message.assistant .msg-content { background: #f5f7fa; color: var(--text-primary); }
.chat-placeholder {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 8px; color: #909399;
}
.chat-input { padding: 16px 20px; border-top: 1px solid var(--border-color); }
.field-item { display: flex; align-items: center; gap: 6px; padding: 6px 0; font-size: 13px; color: var(--text-regular); cursor: default; }
.field-item span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.quick-actions { display: flex; flex-wrap: wrap; gap: 6px; }
.quick-actions .el-button { font-size: 12px; }
</style>
