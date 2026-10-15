import { createContentLoader } from 'vitepress'

export interface CaseEntry { url: string; title: string; source: string; slug: string }
declare const data: CaseEntry[]
export { data }

/** Real-case pages for the home page, read from their frontmatter at build time. */
export default createContentLoader('cases/*.md', {
  transform(pages): CaseEntry[] {
    return pages
      .filter((page) => page.frontmatter.slug)
      .map((page) => ({
        url: page.url,
        title: String(page.frontmatter.title || ''),
        source: String(page.frontmatter.source_type || ''),
        slug: String(page.frontmatter.slug)
      }))
      .sort((a, b) => a.slug.localeCompare(b.slug))
  }
})
