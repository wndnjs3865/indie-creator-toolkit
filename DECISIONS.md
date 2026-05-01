# SEO 사이트 — DECISIONS

## SD-001 — 페이지 패턴 3종 고정
- **결정**: (1) `best-{category}-for-{persona}`, (2) `{a}-vs-{b}`, (3) `free-alternatives-to-{tool}`
- **사유**: 세 패턴이 long-tail SEO 검색어의 80%+ 커버. AI 생성 시 일관성·차별화 동시 확보.
- **재검토**: 6개월차 카니발리제이션 발생 시 패턴 합치거나 신규 패턴 추가.

## SD-002 — 빌드 산출물은 별도 브랜치(`gh-pages`) 미사용. Actions가 직접 Pages에 배포
- **결정**: `actions/deploy-pages@v4` 사용. `site/` 디렉터리는 gitignore.
- **사유**: 단일 브랜치(main) 운영. 워크플로 단순화.

## SD-003 — 데이터 시드는 manual + RSS 결합
- **결정**: `data/seed-tools.json`은 수동 시드(주 1회 추가), `weekly-refresh.yml`이 Product Hunt RSS·AlternativeTo로 metadata 갱신.
- **사유**: 완전 크롤링은 ToS 리스크. 수동 시드는 신뢰도·품질의 차별화 포인트.

## SD-004 — 페이지당 affiliate 최대 5개
- **결정**: 한 페이지에 5개 이상 link 박지 않는다 (Google "low effort affiliate" 페널티 회피).
- **사유**: 외부 SEO 분석 — 5개 이상 페이지는 "AI slop" 신호로 간주됨.

## SD-005 — 모든 내부 링크는 상대경로 (절대경로 금지)
- **결정**: `pages_index.url = f"{slug}/"`(슬래시 없이), nav back-link은 `href="../"`.
- **사유**: GitHub Pages **project site**에서는 절대경로 `/foo/`가 `<user>.github.io/foo/`(사용자 root)로 라우팅됨. 프로젝트 페이지(`<user>.github.io/<repo>/foo/`)에 가려면 상대경로가 필요. 절대경로는 향후 커스텀 도메인 붙일 때 전환 가능.
- **재검토**: 커스텀 도메인 도입 시 `SITE_BASE`를 절대 prefix로 fix.
