import torch
import torch.nn as nn

class HybridCNN_LSTM(nn.Module):
    def __init__(self, input_dim=5, hidden_dim=64, num_layers=2, output_dim=1):
        super(HybridCNN_LSTM, self).__init__()
        
        # 1. CNN Layer (차트의 국소적 패턴 - 캔들 모양 인식)
        self.cnn = nn.Sequential(
            nn.Conv1d(in_channels=input_dim, out_channels=32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2),
            nn.Dropout(0.2)
        )
        
        # 2. LSTM Layer (시간의 흐름 - 추세 인식)
        self.lstm = nn.LSTM(
            input_size=32, 
            hidden_size=hidden_dim, 
            num_layers=num_layers, 
            batch_first=True,
            dropout=0.2
        )
        
        # 3. Fully Connected Layer (최종 판단: 상승 확률 0~1)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, output_dim),
            nn.Sigmoid() # 0~1 사이 확률 출력
        )

    def forward(self, x):
        # x shape: (batch_size, seq_len, input_dim)
        # CNN은 (batch, channel, seq) 형태를 원하므로 transpose
        x = x.transpose(1, 2) 
        
        c_out = self.cnn(x)
        
        # LSTM을 위해 다시 transpose: (batch, seq, feature)
        c_out = c_out.transpose(1, 2)
        
        l_out, _ = self.lstm(c_out)
        
        # 마지막 타임스텝의 히든 스테이트만 사용
        last_hidden = l_out[:, -1, :]
        
        prediction = self.fc(last_hidden)
        return prediction
