# Admin Dashboard

Trading Intelligence Platform 관리자 대시보드

## 📋 기능

### 1. 대시보드 (`/`)
- ✅ 전체 시스템 상태 요약
- ✅ 서비스 헬스 모니터링
- ✅ 실시간 메트릭 표시
- ✅ 데이터베이스 통계

### 2. 사용자 관리 (`/users`)
- ✅ 전체 사용자 목록 (페이지네이션, 검색, 역할 필터)
- ✅ 사용자 정지/활성화
- ✅ 사용자 삭제 (CASCADE)
- ✅ 역할 표시 (user, admin, superadmin)

### 3. 서비스 모니터링 (`/services`)
- ✅ Railway 서비스 상태 실시간 모니터링
- ✅ 서비스별 응답 시간 표시
- ✅ 헬스 체크 (30초마다 자동 갱신)
- ✅ 전체 시스템 상태 집계

### 4. 메트릭 (`/metrics`)
- ✅ 시스템 메트릭 (CPU, 메모리, API 지연, 에러율)
- ✅ 비즈니스 메트릭 (DAU, 레포트 생성 수, 뉴스 분석 수)
- ✅ 시간 범위 필터 (1시간 ~ 7일)
- ✅ 사용자 통계 표시

### 5. 데이터베이스 (`/database`)
- ✅ 테이블 목록 및 통계
- ✅ 행 수, 마지막 업데이트 시간 표시
- ✅ 데이터베이스 헬스 체크
- ✅ 전체 통계 요약

### 6. 로그 (`/logs`)
- ✅ 관리자 활동 로그 조회
- ✅ 액션 필터 (user_update, user_delete 등)
- ✅ 시간 범위 필터
- ✅ 로그 내보내기 (JSON, CSV)

### 7. 설정 (`/settings`)
- ✅ 프로필 정보 표시
- ✅ 보안 설정 (준비 중)
- ✅ 알림 설정
- ✅ 시스템 정보

### 8. 로그인 (`/login`)
- ✅ Supabase Auth 연동
- ✅ admin/superadmin 권한 검증
- ✅ JWT 토큰 자동 갱신

---

## 🚀 로컬 개발 환경 설정

### 1. 환경 변수 설정

`.env` 파일을 생성하고 다음 변수를 설정하세요:

```bash
cp .env.example .env
```

```env
# Supabase 설정
VITE_SUPABASE_URL=https://lrmvoldeyetuzuwuazdm.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key_here

# Admin Service API
VITE_ADMIN_API_URL=http://localhost:8000
```

### 2. 의존성 설치

```bash
npm install
```

### 3. 개발 서버 실행

```bash
npm run dev
# → http://localhost:3001/ 실행
```

### 4. 빌드

```bash
npm run build
```

### 5. 프로덕션 미리보기

```bash
npm run preview
```

---

## 🔐 인증 및 권한

### 로그인 절차

1. **Supabase Auth 로그인**: 이메일/비밀번호
2. **users 테이블 조회**: 사용자 정보 및 role 확인
3. **권한 검증**: role이 `admin` 또는 `superadmin`인지 확인
4. **JWT 토큰 저장**: localStorage에 자동 저장

### 관리자 계정 승격

```sql
-- test@test.com 계정을 admin으로 승격
UPDATE public.users
SET role = 'admin'
WHERE email = 'test@test.com';
```

### 보호된 라우트

`ProtectedRoute` 컴포넌트가 자동으로 인증 확인:
- 로그인하지 않은 사용자 → `/login`으로 리디렉션
- admin/superadmin이 아닌 사용자 → 로그인 거부

---

## 📦 주요 기술 스택

### 프론트엔드
- **React 19**: 최신 React
- **TypeScript**: 타입 안전성
- **Vite**: 빠른 개발 서버
- **TailwindCSS**: 유틸리티 CSS
- **React Router 7**: 클라이언트 라우팅
- **React Query**: 서버 상태 관리
- **Zustand**: 전역 상태 관리
- **Axios**: HTTP 클라이언트

### 라이브러리
- **Lucide React**: 아이콘
- **Recharts**: 차트 (준비 중)
- **date-fns**: 날짜 포맷팅

### 인증
- **Supabase Auth**: JWT 기반 인증
- **Row Level Security**: 데이터베이스 권한 제어

---

## 🎨 디자인 시스템

### 색상 팔레트
- **Primary**: Blue (Tailwind primary-*)
- **Success**: Green (badge-success)
- **Warning**: Yellow (badge-warning)
- **Danger**: Red (badge-danger)
- **Info**: Blue (badge-info)

### 컴포넌트 스타일 클래스
```css
.btn              - 기본 버튼
.btn-primary      - 주요 액션 버튼
.btn-secondary    - 보조 버튼
.btn-danger       - 위험 액션 버튼
.btn-sm           - 작은 버튼

.card             - 카드 컨테이너
.input            - 입력 필드
.table            - 테이블

.badge            - 배지
.badge-success    - 성공 배지
.badge-warning    - 경고 배지
.badge-danger     - 위험 배지
.badge-info       - 정보 배지
```

---

## 📁 프로젝트 구조

```
admin-dashboard/
├── src/
│   ├── components/
│   │   └── Layout.tsx          # 사이드바 + 헤더 레이아웃
│   ├── pages/
│   │   ├── Dashboard.tsx       # 메인 대시보드
│   │   ├── Users.tsx           # 사용자 관리
│   │   ├── Services.tsx        # 서비스 모니터링
│   │   ├── Metrics.tsx         # 메트릭
│   │   ├── Database.tsx        # 데이터베이스
│   │   ├── Logs.tsx            # 로그
│   │   ├── Settings.tsx        # 설정
│   │   └── Login.tsx           # 로그인
│   ├── stores/
│   │   └── authStore.ts        # 인증 상태 관리 (Zustand)
│   ├── lib/
│   │   ├── supabase.ts         # Supabase 클라이언트
│   │   └── adminApi.ts         # Admin API 클라이언트
│   ├── types/
│   │   └── index.ts            # TypeScript 타입 정의
│   ├── App.tsx                 # 메인 앱 컴포넌트
│   ├── main.tsx                # React 엔트리포인트
│   └── index.css               # 전역 스타일
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
└── README.md
```

---

## 🔧 API 연동

### Admin API 클라이언트

`src/lib/adminApi.ts`에서 모든 Admin Service API 호출을 관리합니다.

**자동 JWT 토큰 추가**:
```typescript
// 요청 인터셉터가 자동으로 Authorization 헤더 추가
config.headers.Authorization = `Bearer ${token}`;
```

**사용 예시**:
```typescript
import { adminApi } from '@/lib/adminApi';

// 사용자 목록 조회
const users = await adminApi.getUsers({ limit: 50 });

// 서비스 헬스 체크
const health = await adminApi.getServicesHealth();

// 메트릭 요약
const metrics = await adminApi.getMetricsSummary(24);
```

---

## 📊 React Query 캐싱 전략

### 자동 갱신
- **서비스 헬스**: 30초마다 (`refetchInterval: 30000`)
- **메트릭 요약**: 1분마다 (`refetchInterval: 60000`)
- **DB 헬스**: 1분마다

### 캐시 설정
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5분
    },
  },
});
```

---

## 🚀 Railway 배포 (다음 Phase)

### 환경 변수 설정
```
VITE_SUPABASE_URL=https://lrmvoldeyetuzuwuazdm.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key_here
VITE_ADMIN_API_URL=https://admin-service-production.up.railway.app
```

### 빌드 명령
```bash
npm run build
```

### 실행 명령
```bash
npm run preview
```

---

## 🎯 다음 단계

- **Phase 4**: Railway 배포 설정 (admin-service + admin-dashboard)
- **Phase 5**: 통합 테스트 및 보안 강화

---

**마지막 업데이트**: 2025-10-21
**개발자**: Trading Intelligence Platform Team
