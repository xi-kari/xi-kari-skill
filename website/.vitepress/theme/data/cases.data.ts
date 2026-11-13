import { createContentLoader } from 'vitepress'

export interface CaseEntry { url: string; title: string; source: string; slug: string }
declare const data: CaseEntry[]
export { data }

/**
 * Case pages for the home page, read from their frontmatter at build time.
 * A page with a `slug` has a relation figure of that name and gets a plate;
 * the others are counted so the home page can lead to the full list.
 */
export default createContentLoader('cases/*.md', {
  transform(pages): CaseEntry[] {
    return pages
      .filter((page) => page.frontmatter.kind)
      .map((page) => ({
        url: page.url,
        title: String(page.frontmatter.title || ''),
        source: String(page.frontmatter.source_type || ''),
        slug: String(page.frontmatter.slug || '')
      }))
      .sort((a, b) => a.slug.localeCompare(b.slug) || a.url.localeCompare(b.url))
  }
})
