<script setup lang="ts">
import { reactive, watch } from 'vue'
import { pageHref, useNav, type NavGroup } from '../composables/nav'
import { topLinks } from '../composables/links'

defineProps<{ open: boolean }>()
const emit = defineEmits<{ (e: 'close'): void }>()
const { groups, route, currentGroup } = useNav()

const opened = reactive<Record<string, boolean>>({})
watch(currentGroup, (group) => { if (group) opened[group.text] = true }, { immediate: true })
const isOpen = (group: NavGroup) => opened[group.text] ?? group.items.length <= 3
const toggle = (group: NavGroup) => { opened[group.text] = !isOpen(group) }
const hasLessons = () => groups.value.some((group) => group.items.some((item) => item.lessons))
</script>

<template>
  <nav id="xk-nav" class="xk-nav" aria-label="全书目录">
    <div class="xk-nav__scroll">
      <div class="xk-nav__head">
        <p class="xk-aside__title">全书目录</p>
        <button type="button" class="xk-tool xk-drawer-close" aria-label="关闭目录" @click="emit('close')">
          <svg class="xk-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18" /></svg>
        </button>
      </div>
      <div class="xk-mobile-nav">
        <a
          v-for="item in topLinks"
          :key="item.link"
          :href="pageHref(item.link)"
          :aria-current="item.match(route) ? 'page' : undefined"
          @click="emit('close')"
        >{{ item.text }}</a>
      </div>
      <section
        v-for="group in groups"
        :key="group.text"
        class="xk-nav__group"
        :class="{ 'is-open': isOpen(group) }"
      >
        <button type="button" class="xk-nav__group-head" :aria-expanded="isOpen(group)" @click="toggle(group)">
          <span class="xk-nav__group-title">{{ group.text }}</span>
          <span class="xk-nav__group-count">{{ group.items.length }}</span>
          <svg class="xk-nav__chev xk-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m9 6 6 6-6 6" /></svg>
        </button>
        <div class="xk-nav__group-body" :inert="!isOpen(group) || undefined">
          <ul>
            <li v-for="item in group.items" :key="item.link">
              <a
                class="xk-nav__item"
                :class="{ 'has-no': item.no }"
                :href="pageHref(item.link)"
                :aria-current="item.route === route ? 'page' : undefined"
                @click="emit('close')"
              >
                <span v-if="item.route === route" class="xk-nav__marker" aria-hidden="true" />
                <span v-if="item.no" class="xk-nav__no">{{ item.no }}</span>
                <span class="xk-nav__text">{{ item.title }}</span>
                <span v-if="item.lessons" class="xk-nav__dot" :title="`本篇有 ${item.lessons} 处讲解`" />
              </a>
            </li>
          </ul>
        </div>
      </section>
      <p v-if="hasLessons()" class="xk-nav__note"><span class="xk-nav__dot" aria-hidden="true" />黄点标出已有讲解的篇目。</p>
    </div>
  </nav>
</template>
