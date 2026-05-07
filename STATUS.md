# SEO 사이트 — STATUS (updated 2026-05-07)

## 다음 자동 액션
- GitHub Actions `daily-page.yml`: 매일 06:00 UTC 1페이지 자동 생성·머지·배포 (visual-rich format since 5/7)
- GitHub Actions `weekly-refresh.yml`: 매주 일 03:00 UTC 전체 데이터 갱신
- GitHub Actions `build.yml`: main push 시 자동 빌드 → Pages 배포

## 사이트 URL (라이브)
**https://wndnjs3865.github.io/indie-creator-toolkit/**

## 5/7 ICT Overhaul 완료
- 42 posts 전체 visual-rich (quickpick + tool-card + pros-cons + badges)
- 10 ghost 페이지 source 복원 + 변환
- `generate-page.py` visual-rich 포맷으로 갱신 (daily auto-gen이 일관 포맷 유지)
- 메모리: `plan_c_x402_decision.md` ICT freeze → active overhaul (founder override)

## 다음 내가 할 액션
1. ~~repo + Pages 활성화~~ ✅ 완료
2. ~~Google Search Console 등록~~ ✅ 메타태그 verification 완료 (`base.html.j2:6`)
3. **Amazon Associates 가입** ✅ US LIVE (ID `juwon3865-20`, W8BEN 제출). 한국은 PH 런치 후 traffic 확보 시
4. **PartnerStack / Impact** — 5/5 PartnerStack 거절. PH 런치 (5/12) + traffic 확보 후 5/26경 reapply
5. **Buttondown affiliate** — customer review 통과 후 1-click 활성화 가능
6. **Pricing live 검증** — seed-tools.json 데이터 기반 작성. PH 런치 후 traffic 분석 시점에 일괄 fact-check 권고
7. **이미지 pipeline** — 현재 미지원. 추가 시 4-6h 별도 작업 (templates/build.py 확장 + 스크린샷 수집)

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
- [x] Jinja2 템플릿 3종 (base.html.j2 has full visual-rich CSS: quickpick, tool-card, pros-cons, badges)
- [x] 42 visual-rich 페이지 (5/7 overhaul 완료)
- [x] GitHub Actions: build/deploy + daily/weekly
- [x] seed-keywords.json (페르소나 8 × 카테고리 7 = 56 시드)
- [x] repo + Pages 활성화
- [x] Search Console 등록 (verification meta in base.html.j2)
- [x] Amazon Associates US LIVE
- [x] generate-page.py visual-rich format
- [ ] PartnerStack/Impact reapply (5/26 post-launch)
- [ ] Buttondown affiliate 활성화 (customer review pending)
- [ ] Pricing live 검증 (post-launch)
- [ ] 이미지 pipeline (필요 시 별도)
