<script setup lang="ts">
import { withBase } from 'vitepress'
import FeedbackExplorer from './FeedbackExplorer.vue'
const concepts = [
  { title: '收到意见，就算形成反馈了吗？', term: '反馈与学习', link: '/concepts/feedback.html', description: '沿着信息返回的通道，看看下一步究竟有没有改变。' },
  { title: '每一步都成功，为何仍到不了终点？', term: '局部作用与整链', link: '/concepts/chain.html', description: '把各环节接起来，还要核对同一对象与同一目标。' },
  { title: '每个方案都可行，能一起实施吗？', term: '联合可行性', link: '/concepts/joint-feasibility.html', description: '共享同一份资源时，分别可行还不够。' },
  { title: '平均数说清楚了什么，又藏住了什么？', term: '表示与尺度', link: '/concepts/representation.html', description: '选择怎样的表示，取决于你需要回答什么。' }
]
</script>

<template>
  <main class="handbook-home">
    <section class="home-opening">
      <div class="opening-copy">
        <h1>把概念，放回<br><em>具体的问题。</em></h1>
        <p class="opening-description">从一件真实的事、一个容易混淆的区别开始，理解条件怎样支撑关系，作用怎样传到结果。</p>
        <p class="book-credit">Xikari 著《条件结构与转化论》</p>
        <div class="opening-actions">
          <a class="primary-link" :href="withBase('/concepts/')">从概念开始 <span aria-hidden="true">→</span></a>
          <a class="text-link" :href="withBase('/theory/')">完整阅读原文 <span aria-hidden="true">↗</span></a>
        </div>
      </div>
      <div class="opening-figure">
        <h2>一句“已收到”，离改变还有多远？</h2>
        <FeedbackExplorer />
      </div>
    </section>

    <section class="home-concepts" aria-labelledby="concept-start">
      <div class="section-intro"><h2 id="concept-start">从你真正想问的事开始</h2><p>先把区别看清，再回到它在理论中的位置。</p></div>
      <div class="question-list">
        <a v-for="item in concepts" :key="item.link" :href="withBase(item.link)" class="question-row">
          <span class="question-term">{{ item.term }}</span><div><h3>{{ item.title }}</h3><p>{{ item.description }}</p></div><span class="row-arrow" aria-hidden="true">↗</span>
        </a>
      </div>
      <a class="section-more" :href="withBase('/concepts/')">查看全部概念图解 <span aria-hidden="true">→</span></a>
    </section>

    <section class="home-cases" aria-labelledby="real-cases">
      <div class="section-intro"><h2 id="real-cases">在真实的事情里，看见区别</h2><p>沿着有出处的事实，理解一个概念能帮助我们注意什么。</p></div>
      <div class="case-feature">
        <a :href="withBase('/cases/mars-climate-orbiter.html')" class="case-visual" aria-label="阅读火星气候轨道器案例">
          <svg viewBox="0 0 660 310" role="img" aria-label="地面软件输出与导航输入之间的单位接口示意">
            <rect x="28" y="60" width="235" height="156" rx="5" class="diagram-box"/><rect x="397" y="60" width="235" height="156" rx="5" class="diagram-box"/>
            <text x="54" y="96" class="svg-label">地面软件输出</text><text x="54" y="151" class="svg-unit">lbf·s</text><text x="54" y="187" class="svg-note">磅力秒</text>
            <text x="423" y="96" class="svg-label">导航软件预期</text><text x="423" y="151" class="svg-unit">N·s</text><text x="423" y="187" class="svg-note">牛顿秒</text>
            <path d="M263 138H318 M346 138H397" class="diagram-line"/><path d="M389 131l8 7-8 7" class="diagram-line"/><path d="M327 125l12 26m-12 0 12-26" class="diagram-break"/>
            <text x="330" y="267" text-anchor="middle" class="svg-note">数据到达了，含义并没有正确接上。</text>
          </svg>
        </a>
        <div class="case-copy"><h3><a :href="withBase('/cases/mars-climate-orbiter.html')">一份数据，为什么没有<br>把同一个含义传过去？</a></h3><p>1999 年，火星气候轨道器失联。NASA 的调查把一项关键问题指向地面软件与导航软件之间的单位不一致。</p><p class="case-connection">从这个案例理解：接口、表示，以及局部交付和最终目标的区别。</p><a class="text-link" :href="withBase('/cases/mars-climate-orbiter.html')">阅读案例与来源 <span aria-hidden="true">→</span></a></div>
      </div>
      <a class="case-secondary" :href="withBase('/cases/toyota-andon.html')"><span>生产线上的安灯</span><strong>发现问题之后，谁能让下一步发生改变？</strong><span aria-hidden="true">→</span></a>
      <a class="section-more" :href="withBase('/cases/')">进入真实案例 <span aria-hidden="true">→</span></a>
    </section>

    <section class="home-book" aria-labelledby="read-original">
      <div class="book-spine" aria-hidden="true"><span>Xikari</span><strong>条件结构<br>与转化论</strong><span>对象 · 条件 · 作用与有限行动</span></div>
      <div class="book-description"><h2 id="read-original">每一条理解的路径，<br>都能回到完整原文。</h2><p>十六部分展开对象、关系、尺度、机制与有限选择。四篇附录提供人类变量接口、术语索引、方法内核与领域入口。</p><div class="book-links"><a :href="withBase('/theory/')">按全书顺序阅读 →</a><a :href="withBase('/theory/appendix-b.html')">查找术语与编号 →</a><a :href="withBase('/theory/appendix-d/')">从一个领域进入 →</a><a :href="withBase('/downloads.html')">下载完整原文 →</a></div></div>
    </section>
    <footer class="home-footer"><p>理解从具体的区别开始，也在新的材料与问题中继续。</p><a :href="withBase('/guide/')">使用 Xikari Skill →</a></footer>
  </main>
</template>
