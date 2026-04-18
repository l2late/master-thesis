import torch.nn as nn


class MLP(nn.Module):
    def __init__(
        self,
        in_channels,
        out_channels,
        hidden_dims=[32, 32, 32],
        activation="relu",
        dropout=0.3,
    ):
        super(MLP, self).__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.hidden_dims = hidden_dims
        self.activation = activation
        self.dropout = dropout

        assert len(hidden_dims) >= 2
        sizes = list(zip(hidden_dims[:-1], hidden_dims[1:]))

        ## Only non-decreasing activation functions
        if self.activation == "relu":
            self._activation = nn.ReLU()
        elif self.activation == "elu":
            self._activation = nn.ELU()
        elif self.activation == "celu":
            self._activation = nn.CELU()
        elif self.activation == "softplus":
            self._activation = nn.Softplus()
        else:
            raise Exception("Activation is not specified or unknown.")

        # First layer has no convexity constraints
        self.first_layer = nn.Sequential(
            nn.Linear(in_channels, hidden_dims[0], bias=True),
            self._activation,
            nn.Dropout(dropout),
        )

        self.linear_layers = nn.ModuleList(
            [
                nn.Sequential(
                    nn.Linear(in_channels, out_channels, bias=True),
                    self._activation,
                    nn.Dropout(dropout),
                )
                for (in_channels, out_channels) in sizes
            ]
        )

        self.last_layer = nn.Linear(hidden_dims[-1], out_channels, bias=False)

    def forward(self, input):
        output = self.first_layer(input)
        for linear_layer in self.linear_layers:
            output = linear_layer(output)

        return self.last_layer(output)
