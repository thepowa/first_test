이 모델은 solar-mini 모델을 사용하여 환자 의료 데이터를 현장에서 활용하여 응급 의료를 돕는 시스템입니다

medicial_response
├── app/                    
│   └── app.py                      
├── spine/
│   ├── .env
│   └── requirements.txt              # pip install -r config/requirements.txt        
├── Fieldkit/                         
                                      # 전체 과정 관리: 현장 환자별 정상범위 설정 -> 환자 상태 판단 정보 입력 -> 정상범위 설정 / 프로토콜 문서, 데이터 확인 -> AI가 답변으로 결과 반환

│   └── app.py                       
                                      # 4가지 작업: GCS 점수 입력 + SPO2 수치 입력 + OPQRST 및 SAMPLE 정보 입력 / 입력된 정보 베이스로 대응 절차 생성
├── record/
│   ├── feedback.py                   # 실시간 출력 관련 피드백 수집
│   └── prompt.md
