export interface TopLink { text: string; link: string; match: (route: string) => boolean }

/** The sections named in the top bar (and at the head of the index on narrow screens). */
export const topLinks: TopLink[] = [
  { text: '原文', link: '/theory/', match: (r) => r.startsWith('/theory/') && r !== '/theory/appendix-b' },
  { text: '术语', link: '/theory/appendix-b', match: (r) => r === '/theory/appendix-b' },
  { text: '讲解', link: '/concepts/', match: (r) => r.startsWith('/concepts/') },
  { text: '案例', link: '/cases/', match: (r) => r.startsWith('/cases/') },
  { text: '指南', link: '/guide/', match: (r) => r.startsWith('/guide/') || r === '/downloads' }
]
