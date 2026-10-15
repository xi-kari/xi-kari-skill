<script setup lang="ts">
defineProps<{ name: string }>()
</script>

<template>
  <span class="xk-mod__icon" aria-hidden="true">
    <svg viewBox="0 0 24 24" focusable="false">
      <template v-if="name === 'terms'">
        <path d="M3.5 7.5h10l5.5 4.5-5.5 4.5h-10z" /><circle cx="7.5" cy="12" r="1.2" />
      </template>
      <template v-else-if="name === 'quote'">
        <path d="M9 4H5v8M15 20h4v-8" /><path d="M9 9h6M9 13h6" stroke-dasharray="2 2" />
      </template>
      <template v-else-if="name === 'steps'">
        <circle cx="6" cy="5" r="2" /><circle cx="6" cy="12" r="2" /><circle cx="6" cy="19" r="2" />
        <path d="M6 7v3M6 14v3" stroke-dasharray="1.5 1.5" /><path d="M11 5h9M11 12h9M11 19h6" />
      </template>
      <template v-else-if="name === 'split'">
        <circle cx="12" cy="12" r="8.5" /><path d="M8 10.2h8M8 13.8h8M14.2 7.5l-4.4 9" />
      </template>
      <template v-else-if="name === 'figure'">
        <path d="M4 8V4h4M16 4h4v4M20 16v4h-4M8 20H4v-4" /><circle cx="9" cy="14.5" r="1.6" /><circle cx="15" cy="9.5" r="1.6" /><path d="M10.3 13.4 13.7 10.6" />
      </template>
      <template v-else-if="name === 'scenario'">
        <rect x="4" y="4" width="16" height="16" rx="1.5" stroke-dasharray="3 2.4" /><path d="M8.5 15.5l3-4 2 2 2-3" />
      </template>
      <template v-else-if="name === 'model'">
        <path d="M4 8h16M4 16h16" /><circle cx="9" cy="8" r="2.2" /><circle cx="15" cy="16" r="2.2" />
      </template>
      <template v-else-if="name === 'case'">
        <path d="M6 3h8.5L18 6.5V21H6z" /><path d="M14.5 3v3.5H18M9 11h6M9 14.5h6M9 18h4" />
      </template>
      <template v-else-if="name === 'limit'">
        <circle cx="12" cy="12" r="8.5" /><path d="M6 6l12 12" />
      </template>
      <template v-else-if="name === 'check'">
        <rect x="4" y="4" width="16" height="16" rx="2" /><path d="M9.6 9.6a2.4 2.4 0 1 1 3.4 2.2c-.6.3-1 .8-1 1.4v.6" /><circle cx="12" cy="16.6" r=".6" fill="currentColor" />
      </template>
      <template v-else-if="name === 'summary'">
        <path d="M5 6h14M5 10.5h10" /><path d="M4 16.5c3-1.6 6.5-1.6 9.5 0s5.2 1.4 6.5.3" stroke-width="2" />
      </template>
      <template v-else>
        <circle cx="12" cy="12" r="8.5" /><path d="M3.5 12h17" />
      </template>
    </svg>
  </span>
</template>
