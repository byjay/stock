import torch
import torch.nn as nn

class DeepEyesModel(nn.Module):
    """
    [ISATS Ferrari Brain] 하이브리드 인공지능 두뇌
    - 설계: CNN(패턴) + LSTM(추세) 결합
    """
    def __init__(self, input_dim=10, hidden_dim=128):
        super(DeepEyesModel, self).__init__()
        
        # 차트 시각 패턴 인식 (CNN)
        self.cnn = nn.Sequential(
            nn.Conv1d(input_dim, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(2)
        )
        
        # 시계열 흐름 파악 (LSTM)
        self.lstm = nn.LSTM(32, hidden_dim, batch_first=True)
        
        # 최종 판단 (FC)
        self.fc = nn.Linear(hidden_dim, 3) # Buy, Hold, Sell

    def forward(self, x):
        # x: (Batch, Features, Seq)
        x = self.cnn(x)
        x = x.transpose(1, 2) # (Batch, Seq, Features)
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])
