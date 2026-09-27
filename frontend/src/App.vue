<template>
  <div class="app-container">
    <header class="app-header">
      <h1>BidAlert - 中标未签约项目进度追踪</h1>
      <nav class="nav-tabs">
        <router-link to="/" class="nav-tab" :class="{ active: route.path === '/' }" @click.native="navigate('/')">总览</router-link>
        <router-link to="/board" class="nav-tab" :class="{ active: route.path === '/board' }" @click.native="navigate('/board')">看板</router-link>
        <router-link to="/list" class="nav-tab" :class="{ active: route.path === '/list' }" @click.native="navigate('/list')">列表</router-link>
        <router-link to="/manage" class="nav-tab" :class="{ active: route.path === '/manage' }" @click.native="navigate('/manage')">管理</router-link>
      </nav>
    </header>
    <main class="app-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
const route = useRoute()
const router = useRouter()
const navigate = (path) => router.push(path)
</script>
