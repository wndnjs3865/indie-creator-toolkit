# SEO 사이트 — STATUS

## 다음 자동 액션
- GitHub Actions `daily-page.yml`: 매일 06:00 UTC 1페이지 자동 생성·머지·배포
- GitHub Actions `weekly-refresh.yml`: 매주 일 03:00 UTC 전체 데이터 갱신

## 다음 내가 할 액션
1. repo 생성 후 Settings → Pages → Source: "GitHub Actions" 활성화
2. Search Console에 사이트 등록 + sitemap 제출 (Pages 도메인 확정 후)
3. Amazon Associates 가입 (글로벌 + 한국 둘 다)
4. PartnerStack / Impact 가입 + 시드 affiliate 5개 등록 → `data/affiliates.json` 채우기

## 아키텍처
```
data/
  seed-keywords.json    ← 수동 시드 + 자동 확장
  seed-tools.json       ← 도구 카탈로그 (id, name, category, affiliate_url, price, free_tier)
  affiliates.json       ← affiliate 링크 매핑
content/
  *.md                  ← 페이지 마크다운 (frontmatter + 본문)
templates/
  base.html.j2          ← 공통 레이아웃
  comparison.html.j2    ← 비교 페이지
  list.html.j2          ← 리스트(Best X for Y) 페이지
  index.html.j2         ← 홈
scripts/
  build.py              ← Markdown + data → HTML 빌드
  generate-page.py      ← Claude 호출 없이 룰 기반 + 데이터 페이지 생성
  fetch-data.py         ← Product Hunt RSS, AlternativeTo 크롤링
site/                   ← 빌드 산출물 (gh-pages 배포 대상)
```

## 페이지 패턴 (3종)
1. **`best-{category}-for-{persona}`** — "Best podcast hosting for solo podcasters"
2. **`{tool-a}-vs-{tool-b}`** — "Notion vs Obsidian for screenwriters"
3. **`free-alternatives-to-{tool}`** — "Free alternatives to Substack"

## 시드 카테고리 (페르소나 × 카테고리 = 페이지 수천 건 가능)
- 페르소나: solo podcasters, indie game devs, screenwriters, illustrators, newsletter writers, audiobook narrators, indie filmmakers, music producers
- 카테고리: hosting, editing, distribution, analytics, monetization, collaboration, project mgmt

## 수익 채널
- Amazon Associates (하드웨어: 마이크, 그래픽 태블릿)
- PartnerStack (Notion 30%, ClickUp 20% recurring)
- Impact (Adobe Creative Cloud 8%)
- ConvertKit / ConvertCommerce (newsletter 30%)
- 직접 affiliate (Substack, Squarespace, Webflow)

## 현재 상태
- [x] 디렉터리 골격
- [x] Python 빌더 (build.py)
- [x] Jinja2 템플릿 3종
- [x] 샘플 페이지 5건 (1 fully fleshed + 4 stubs)
- [x] GitHub Actions: build/deploy + daily/weekly
- [x] seed-keywords.json (페르소나 8 × 카테고리 7 = 56 시드)
- [ ] repo 생성 → Pages 활성화
- [ ] affiliate 가입 + 링크 등록
- [ ] Search Console 등록
