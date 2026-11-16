<script setup lang="ts">
import { useLocale } from '../composables/locale'
const { t, isEnglish, localePath } = useLocale()
import { reactive, watch } from 'vue'
import { pageHref, useNav, type NavGroup } from '../composables/nav'
import { projectHome, useTopLinks } from '../composables/links'

defineProps<{ open: boolean }>()
const emit = defineEmits<{ (e: 'close'): void }>()
const { groups, route, currentGroup } = useNav()
const topLinks = useTopLinks()

const opened = reactive<Record<string, boolean>>({})
watch(currentGroup, (group) => { if (group) opened[group.text] = true }, { immediate: true })
const isOpen = (group: NavGroup) => opened[group.text] ?? group.items.length <= 3
const toggle = (group: NavGroup) => { opened[group.text] = !isOpen(group) }
const hasLessons = () => groups.value.some((group) => group.items.some((item) => item.lessons))
</script>

<template>
  <nav id="xk-nav" class="xk-nav" :aria-label="t('全书目录', 'Book contents')">
    <div class="xk-nav__scroll">
      <div class="xk-nav__head">
        <p class="xk-aside__title">{{ t('全书目录', 'Book contents') }}</p>
        <button type="button" class="xk-tool xk-drawer-close" :aria-label="t('关闭目录', 'Close contents')" @click="emit('close')">
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
        <a :href="projectHome" target="_self">{{ t('项目主页', 'Project') }}</a>
      </div>
      <section
        v-for="group in groups"
        :key="group.text"
        class="xk-nav__group"
        :class="{ 'is-open': isOpen(group) }"
      >
        <button type="button" class="xk-nav__group-head" :aria-expanded="isOpen(group)" @click="toggle(group)">
          <span class="xk-nav__group-title">{{ group.text }}</span>
          <span class="xk-nav__group-count" :title="t(`${group.items.length} 篇`, `${group.items.length} pages`)">{{ group.items.length }}</span>
          <span class="xk-nav__group-fold" aria-hidden="true"><svg class="xk-nav__chev xk-icon" viewBox="0 0 24 24"><path d="m9 6 6 6-6 6" /></svg></span>
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
                <span v-if="item.no" class="xk-nav__no">{{ item.no }}</span>
                <span class="xk-nav__text">{{ item.title }}</span>
                <span v-if="item.lessons" class="xk-nav__count" :title="t(`本篇有 ${item.lessons} 处讲解`, `${item.lessons} reading notes on this page`)">{{ item.lessons }}</span>
                <span v-if="item.route === route" class="xk-nav__marker" aria-hidden="true" />
              </a>
            </li>
          </ul>
        </div>
      </section>
      <p v-if="hasLessons()" class="xk-nav__note">{{ t('每条右格的数字，是这一篇已有的讲解处数。', 'Numbers on the right count the available reading notes for each page.') }}</p>
    </div>
  </nav>
</template>
