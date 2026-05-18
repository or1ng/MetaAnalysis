<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <img src="https://api.iconify.design/fluent:data-bar-vertical-24-filled.svg?color=%233a6fd8" alt="logo" class="login-logo" />
        <h1>MetaAnalysis元析智能</h1>
        <p>新一代智能数据分析平台</p>
      </div>
      <el-form :model="form" :rules="rules" ref="formRef" @keyup.enter="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" size="large" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" size="large" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" :loading="loading" @click="handleLogin" style="width:100%">
            登 录
          </el-button>
        </el-form-item>
        <div class="login-footer">
          <el-button type="primary" link @click="goRegister">注册账号</el-button>
          <el-button type="info" link>游客试用</el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../../store/index'
import { login, register } from '../../api/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  await formRef.value.validate()
  loading.value = true
  try {
    const res = await login(form)
    userStore.setLogin(res.data)
    ElMessage.success('登录成功')
    router.push('/home')
  } catch (e) {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}

function goRegister() {
  ElMessage.info('注册功能开发中')
}
</script>

<style scoped>
.login-container {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
}
.login-card {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
.login-header { text-align: center; margin-bottom: 32px; }
.login-logo { width: 48px; height: 48px; margin-bottom: 12px; }
.login-header h1 { font-size: 22px; color: #1e293b; margin-bottom: 4px; }
.login-header p { color: #909399; font-size: 14px; }
.login-footer { display: flex; justify-content: space-between; }
</style>
