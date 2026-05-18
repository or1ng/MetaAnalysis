import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '访客')
  const userId = ref(Number(localStorage.getItem('userId')) || 0)

  function setLogin(data) {
    token.value = data.access_token
    username.value = data.username
    userId.value = data.user_id
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('username', data.username)
    localStorage.setItem('userId', data.user_id)
  }

  function logout() {
    token.value = ''
    username.value = '访客'
    userId.value = 0
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('userId')
  }

  return { token, username, userId, setLogin, logout }
})
