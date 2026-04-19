# User Role

Claude Code를 프로젝트 개발에 효율적으로 활용하는 방안을 지속적으로 연구하는 것이 주요 업무.
단순 개발 보조 외에도 Claude Code 활용 패턴, 워크플로우 최적화, 자동화 방안 등을 탐구함.

---

# Project Overview

법인카드 내역 기반 회계 계정/약정항목 추천 AI 시스템

## 목적
- 회계전표 데이터를 Qdrant 벡터 DB에 업로드
- 법인카드 내역 입력 시 Qdrant 유사도 검색으로 계정과목, 약정항목 등 추천

## 현황
- 핵심 기능 구현 완료, 고객사 1차 판매 진행됨 (상용 서비스 단계)
- 현재는 고도화를 위한 연구 단계 — 추천 정확도 향상, 워크플로우 최적화, 새로운 기술 도입 검토 등

## 기술 스택
- **Backend**: Python, FastAPI
- **Vector DB**: Qdrant
- **Frontend**: JavaScript, HTML (관리자 웹 콘솔)
