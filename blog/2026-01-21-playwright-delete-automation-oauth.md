---
title: "[Playwright] 삭제 버튼 52번 누르기 싫어서 만든 자동화 스크립트 (feat. OAuth 로그인 뚫기)"
date: "2026-01-21"
tags: [playwright, automation, oauth, session, accessibility]
---

> "개발자의 3대 미덕은 나태(Laziness), 성급함(Impatience), 오만(Hubris)이다." - 래리 월(Larry Wall)

어느 평화로운 오후, QueryPie Knowledge 페이지 관리 화면을 보며 깊은 한숨을 내쉬었습니다. 테스트를 위해 생성했던 52개의 데이터가 저를 비웃듯 줄지어 있었기 때문이죠.

각 항목을 삭제하는 프로세스는 다음과 같았습니다.

1. 메뉴 버튼 클릭 (`...`)
2. 'Delete Source' 메뉴 클릭
3. 최종 확인 모달에서 'Delete' 버튼 클릭

**52개 항목 × 3번의 클릭 = 총 156번의 클릭.**
단순 반복 노동을 혐오하는 개발자로서, 이 짓을 손으로 할 순 없었습니다.

*"개발자는 게으르다. 그래서 자동화한다."*

저는 곧바로 **Playwright**를 켜고 Claude에게 물었습니다. "이거 자동화할 수 있지?"

---

## 1. 도구의 선택: Playwright Codegen

가장 먼저 꺼내 든 카드는 Playwright의 강력한 기능인 `codegen`이었습니다. 브라우저에서의 동작을 녹화해 코드로 변환해 주는 기능이죠.

```bash
npx playwright codegen https://example.com

```

브라우저와 Inspector 창이 열리고, 제가 클릭하는 모든 동작이 실시간으로 프로덕션 레벨의 테스트 코드로 변환됩니다. 셀렉터(Selector)를 일일이 찾을 필요가 없으니 이보다 편할 수 없습니다.

하지만 곧바로 첫 번째 난관에 봉착했습니다.

## 2. 첫 번째 난관: OAuth 로그인과 프로필 충돌

자동화 대상 서비스는 **Google OAuth + Okta MFA** 조합을 사용하고 있었습니다. 자동화 봇에게는 최악의 천적이죠.

Codegen을 사용하려면 로그인이 선행되어야 하는데, 이미 Chrome이 실행 중인 상태에서 Playwright가 프로필에 접근하려 하니 충돌이 발생했습니다.

```
Error: Profile in use

```

"자동화를 위해 띄워둔 30개의 탭을 모두 닫으라고?"
물론 그럴 순 없었습니다.

### 해결책: 브라우저 격리 (feat. Firefox)

해결책은 의외로 간단했습니다. 일상 업무는 Chrome에서, 자동화는 **Firefox**에서 돌리는 '철저한 분업'입니다.

```javascript
const { firefox } = require('playwright');
const browser = await firefox.launch({ headless: false });

```

여기서 중요한 점은 Playwright가 사용하는 Firefox는 제 PC에 설치된 시스템 브라우저가 아니라, **Playwright가 샌드박스 형태로 자체 다운로드한 바이너리**라는 것입니다. 덕분에 기존 Chrome 세션과의 충돌 없이 깔끔한 환경을 얻을 수 있었습니다.

---

## 3. 두 번째 난관: 인증 상태 유지 (Session Storage)

Firefox로 환경은 분리했지만, Playwright의 격리된 환경 탓에 매번 로그인을 새로 해야 하는 문제가 남았습니다. 특히 MFA가 걸린 OAuth 로그인을 스크립트로 뚫는 건 배보다 배꼽이 더 큰 작업입니다.

### 전략: 수동 로그인 + 세션 스냅샷

완전 자동화를 고집하기보다 현실적인 타협안을 선택했습니다.
**"최초 1회는 사람이 직접 로그인하고, 그 세션 정보를 저장해서 재사용하자."**

### Step 1. URL 변경 감지로 로그인 완료 판단

터미널 입력을 기다리는 방식(stdin)은 브라우저 자동화와 섞였을 때 불안정했습니다. 대신 URL이 로그인 페이지에서 메인 서비스로 리다이렉트 되는 것을 감지하도록 구현했습니다.

```javascript
// 로그인 페이지라면 수동 로그인을 대기
const needsLogin = page.url().includes('login');

if (needsLogin) {
  console.log('⏳ 브라우저에서 로그인을 진행해주세요...');

  // OAuth -> Okta -> Redirect 까지 충분한 시간 대기
  await page.waitForURL(targetUrl, { timeout: 300000 });

  // 로그인 성공 후 세션 저장
  await context.storageState({ path: 'auth.json' });
  console.log('💾 세션 저장 완료!');
}

```

### Step 2. `storageState`로 영혼까지 백업하기

Playwright의 `storageState` 메서드는 현재 브라우저 컨텍스트의 **쿠키(Cookies)**와 **로컬 스토리지(LocalStorage)**를 통째로 JSON 파일로 덤프합니다.

```json
// auth.json 예시
{
  "cookies": [
    { "name": "session_id", "value": "abc123...", "domain": ".querypie.com" },
    { "name": "auth_token", "value": "xyz789..." }
  ],
  "origins": [
    { "origin": "https://app.querypie.com", "localStorage": [...] }
  ]
}

```

이제 다음 실행부터는 이 파일을 로드하기만 하면 됩니다.

```javascript
// 저장된 세션 파일이 존재하면 로드
if (fs.existsSync('auth.json')) {
  context = await browser.newContext({ storageState: 'auth.json' });
}

```

### Step 3. 세션 만료 처리 (Self-Healing)

만약 세션이 만료되었다면? 페이지는 다시 로그인 화면으로 튕길 겁니다. 이를 감지해 만료된 파일을 삭제하고 다시 수동 로그인을 유도하는 로직을 추가하여 스크립트의 견고함을 더했습니다.

---

## 4. 삭제 로직 구현: 접근성 셀렉터의 승리

로그인 문제를 해결했으니, 남은 건 반복 삭제뿐입니다. 여기서 Playwright의 진가가 발휘됩니다.

```javascript
while (true) {
  // 'Open menu'라는 라벨을 가진 버튼 탐색
  const menuButtons = page.getByLabel('Open menu');

  // 더 이상 삭제할 버튼이 없으면 종료
  if (await menuButtons.count() === 0) break;

  await menuButtons.first().click();
  await page.getByRole('menuitem', { name: 'Delete Source' }).click();
  await page.getByRole('button', { name: 'Delete' }).click();

  // UI 갱신 대기 (Optional)
  await page.waitForTimeout(500);
}

```

### Tip: `getByRole` & `getByLabel`

과거에는 CSS 클래스(`.btn-delete`, `.menu-item-3`)를 사용했지만, 이는 디자인이 변경되면 쉽게 깨집니다. 반면 **접근성(Accessibility) 기반 셀렉터**인 `getByLabel`, `getByRole`은 스크린 리더를 위해 제공되는 속성이므로 UI가 바뀌어도 유지될 가능성이 훨씬 높습니다.

> "접근성을 지키는 것은 장애인 사용자뿐만 아니라, 자동화 봇을 만드는 개발자에게도 축복입니다."

---

## 결론: 156번의 클릭을 6줄의 코드로

스크립트를 실행하자 터미널에는 아름다운 로그가 찍히기 시작했습니다.

```
...
🗑️  50개 삭제됨
🗑️  51개 삭제됨
🗑️  52개 삭제됨
📊 총 52개 삭제 완료
✨ Done!

```

156번의 클릭 노동이 `node delete-script.js` 엔터 한 번으로 해결되었습니다. 저는 팔짱을 끼고 커피를 마시며, 화면 속 데이터가 사라지는 것을 구경만 하면 되었습니다.

### TIL (Today I Learned)

1. **Playwright Codegen**: 초기 보일러플레이트 코드를 짜는 데 최고의 도구다.
2. **브라우저 분리**: Chrome 프로필 충돌이 날 땐, 쿨하게 Firefox를 쓰자.
3. **URL 기반 감지**: OAuth 로그인 흐름 제어에는 `waitForURL`이 가장 안정적이다.
4. **storageState**: 한 번 로그인한 세션을 저장하면 개발의 질이 달라진다.
5. **접근성 셀렉터**: `getByRole`, `getByLabel`은 CSS 셀렉터보다 훨씬 견고(Robust)하다.

게으름은 미덕입니다. 단, 그것이 **'자동화'**로 이어질 때만 말이죠.
