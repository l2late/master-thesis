import torch as th
import torch.nn as nn
import torch.nn.functional as F


class NonNegativeLinear(nn.Linear):
    def __init__(self, in_features: int, out_features: int, bias: bool = True):
        super().__init__(in_features, out_features)
        self.weight = nn.Parameter(th.Tensor(out_features, in_features))
        if bias:
            self.bias = nn.Parameter(th.Tensor(out_features))
        else:
            self.bias = None
        # nn.init.kaiming_normal_(self.weight, nonlinearity="relu")
        nn.init.uniform_(self.weight, 0, (6 / (in_features + out_features)) ** 0.5)

    def forward(self, input):
        # Original Implementation:
        # weight = F.relu(self.weight)
        # return F.linear(input, weight, self.bias)

        self.weight.data = F.relu(
            self.weight.data
        )  # in place projection. Better because it bypasses ReLU’s derivative by clamping weights after parameter updates. Gradients flow through self.weight before clamping, allowing weights to adjust freely without gradient starvation.
        return F.linear(input, self.weight, self.bias)
