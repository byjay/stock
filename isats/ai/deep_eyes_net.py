import torch
import torch.nn as nn
import torch.nn.functional as F

class DeepEyesModel(nn.Module):
    """
    [ISATS Deep Eyes] 시장의 눈 (The Eye of Market)
    - 역할: CNN으로 차트 패턴을, LSTM으로 호가 흐름을 읽어 10틱 뒤 등락을 예측
    - 입력: (Batch, Features, Sequence_Length)
    """
    def __init__(self, input_dim=10, hidden_dim=128, num_layers=2, output_dim=3):
        super(DeepEyesModel, self).__init__()
        
        # ---------------------------------------------------------
        # 1. CNN Block: 차트의 시각적 패턴(굴곡, 지지/저항) 추출
        # ---------------------------------------------------------
        self.cnn_layer = nn.Sequential(
            # 1단계: 단순 패턴 인식
            nn.Conv1d(in_channels=input_dim, out_channels=32, kernel_size=3, padding=1),
            nn.BatchNorm1d(32),
            nn.LeakyReLU(0.1),
            nn.MaxPool1d(kernel_size=2),
            
            # 2단계: 복합 패턴 인식
            nn.Conv1d(in_channels=32, out_channels=64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.LeakyReLU(0.1),
            nn.MaxPool1d(kernel_size=2)
        )
        
        # ---------------------------------------------------------
        # 2. LSTM Block: 호가창의 시간적 흐름(Momentum) 기억
        # ---------------------------------------------------------
        self.lstm = nn.LSTM(
            input_size=64,  # CNN 출력 채널 수와 맞춰줌
            hidden_size=hidden_dim, 
            num_layers=num_layers, 
            batch_first=True,
            dropout=0.2
        )
        
        # ---------------------------------------------------------
        # 3. Decision Head: 최종 매수/매도 판단
        # ---------------------------------------------------------
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, output_dim) # [0:매도, 1:관망, 2:매수]
        )

    def forward(self, x):
        # x shape: (Batch, Features, Sequence_Length)
        
        # 1. 시각 정보 추출 (CNN)
        x = self.cnn_layer(x) 
        
        # 2. 차원 변환 (LSTM 입력용): (Batch, Channels, Length) -> (Batch, Length, Channels)
        x = x.permute(0, 2, 1) 
        
        # 3. 시계열 기억 (LSTM)
        # self.lstm은 (out, (h_n, c_n))을 반환함
        out, _ = self.lstm(x)
        
        # 4. 마지막 시점의 판단만 사용 (Many-to-One)
        last_out = out[:, -1, :] 
        
        # 5. 최종 확률 계산
        logits = self.fc(last_out)
        return F.softmax(logits, dim=1)

# ==========================================
# [검증 모듈] 에이전트가 이 파일을 실행하면 즉시 테스트됨
# ==========================================
if __name__ == "__main__":
    print("🧠 [System] Deep Eyes 두뇌 가동 테스트 시작...")
    
    # 1. 가상 데이터 생성 (배치:1, 특징:10개, 시간:60틱)
    dummy_input = torch.randn(1, 10, 60) 
    print(f"   - 입력 데이터 형태: {dummy_input.shape}")

    # 2. 모델 로드
    model = DeepEyesModel()
    
    # 3. 추론 시도
    try:
        output = model(dummy_input)
        print(f"   - 예측 결과(확률): {output.detach().numpy()}")
        print("✅ [Success] 모델 구조 정상. 작전 투입 준비 완료.")
    except Exception as e:
        print(f"❌ [Fail] 모델 오류 발생: {e}")
