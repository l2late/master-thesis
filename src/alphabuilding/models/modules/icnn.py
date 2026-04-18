from collections import OrderedDict

import torch as th
import torch.nn as nn

from layers.convex_layers import NonNegativeLinear


class ICNN(nn.Module):
    def __init__(
        self,
        in_channels,
        out_channels,
        hidden_layer_sizes: list[int],
        activation="relu",
    ):
        """
        Initialize an ICNN (Input Convex Neural Network) model.

        Args:
            in_channels (int): Number of input features.
            out_channels (int): Number of output features.
            hidden_layer_sizes (list[int]): List of sizes of the hidden layers.
            activation (str): Activation function to use. Options include 'relu', 'leakyrelu', 'elu', 'celu', and 'softplus'.
        """
        super(ICNN, self).__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.hidden_layer_sizes = hidden_layer_sizes
        self.activation = activation

        assert len(self.hidden_layer_sizes) >= 2
        sizes = list(zip(self.hidden_layer_sizes[:-1], self.hidden_layer_sizes[1:]))

        ## Only non-decreasing activation functions
        if self.activation == "relu":
            self._activation = nn.ReLU()
        elif self.activation == "leakyrelu":
            self._activation = nn.LeakyReLU()
        elif self.activation == "elu":
            self._activation = nn.ELU()  # smooth
        elif self.activation == "celu":
            self._activation = nn.CELU()  # smoother
        elif self.activation == "softplus":
            self._activation = nn.Softplus()  # smoothest
        else:
            raise Exception("Activation is not specified or unknown.")

        # First layer has no convexity constraints
        self.first_layer = nn.Sequential(
            nn.Linear(in_channels, self.hidden_layer_sizes[0], bias=True),
            self._activation,
        )

        self.convex_layers = nn.ModuleList(
            [
                nn.Sequential(
                    nn.Linear(in_channels, out_channels, bias=True),
                    self._activation,
                )
                for (in_channels, out_channels) in sizes
            ]
        )

        self.last_layer = nn.Linear(
            self.hidden_layer_sizes[-1], out_channels, bias=False
        )

    def forward(self, input):
        output = self.first_layer(input)
        for convex_layer in self.convex_layers:
            output = convex_layer(output)

        return self.last_layer(output)

    def _get_required_non_negative_weights(self):
        return [layer[0].weight for layer in self.convex_layers] + [
            self.last_layer.weight
        ]

    def convexify(self):
        for weight in self._get_required_non_negative_weights():
            weight.data.relu_()

    def is_input_convex(self):
        weights = self._get_required_non_negative_weights()
        for weight in weights:
            if not is_non_negative(weight):
                return False
        return True


def is_non_negative(tensor: th.Tensor) -> bool:
    if (tensor < 0).sum() > 0:
        return False
    else:
        return True


class ICNN_ReLU(nn.Module):
    def __init__(
        self,
        in_channels,
        out_channels,
        hidden_dims=[32, 32, 32],
        activation="relu",
    ):
        super(ICNN_ReLU, self).__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.hidden_layer_sizes = hidden_dims
        self.activation = activation

        assert len(hidden_dims) >= 2
        sizes = list(zip(hidden_dims[:-1], hidden_dims[1:]))

        ## Only non-decreasing activation functions
        if self.activation == "relu":
            self._activation = nn.ReLU()
        elif self.activation == "leakyrelu":
            self._activation = nn.LeakyReLU()
        elif self.activation == "elu":
            self._activation = nn.ELU()
        elif self.activation == "celu":
            self._activation = nn.CELU()
        elif self.activation == "softplus":
            self._activation = nn.Softplus()
        else:
            raise Exception("Activation is not specified or unknown.")

        # First layer has no convexity constraints
        self.first_layer = nn.Sequential()
        self.first_layer.add_module(
            "first_layer",
            nn.Linear(in_channels, hidden_dims[0], bias=True),
        )
        self.first_layer.add_module("first_layer_activation", self._activation)

        self.convex_layers = nn.ModuleList(
            [
                nn.Sequential(
                    OrderedDict(
                        [
                            # Linear layer with index-based name
                            (
                                f"convex_{i}_linear",
                                NonNegativeLinear(in_channels, out_channels),
                            ),
                            # Activation with matching index
                            (f"convex_{i}_activation", self._activation),
                        ]
                    )
                )
                for i, (in_channels, out_channels) in enumerate(sizes)
            ]
        )

        self.last_layer = NonNegativeLinear(hidden_dims[-1], out_channels, bias=False)

    def forward(self, input):
        output = self.first_layer(input)
        for convex_layer in self.convex_layers:
            output = convex_layer(output)
            # assert not th.isnan(output).any(), f"NaN at convex_layer {ii}"

        return self.last_layer(output)


class ResidualMLP(nn.Module):
    def __init__(
        self,
        input_dim: int = 3,
        output_dim: int = 1,
        layer_size: int = 8,
        loss_fn=nn.MSELoss(),
    ):
        super(ResidualMLP, self).__init__()
        self.loss_fn = loss_fn
        self.hidden_dim = [layer_size, layer_size, layer_size]

        if isinstance(self.hidden_dim, int):
            self.hidden_dim = [self.hidden_dim]
        self.hidden_layers = nn.ModuleList(
            [
                nn.Linear(in_dim, out_dim)
                for in_dim, out_dim in zip(
                    [input_dim] + self.hidden_dim[:-1], self.hidden_dim
                )
            ]
        )
        self.output_layer = nn.Linear(self.hidden_dim[-1], output_dim)

    def forward(self, Te, T, Q_dot_in, T_target):
        x = th.cat([Te, T, Q_dot_in], dim=1)
        for layer in self.hidden_layers:
            x = layer(x)
            x = th.relu(x)
        x = self.output_layer(x)
        T_next = T + x
        loss = self.loss_fn(T_next, T_target)
        return loss, T_next

    def convexify(self):
        pass

    def is_input_convex(self) -> bool:
        return False


class MLP(nn.Module):
    def __init__(
        self,
        input_dim: int = 3,
        output_dim: int = 1,
        layer_size: int = 8,
        loss_fn=nn.MSELoss(),
    ):
        super(MLP, self).__init__()
        self.loss_fn = loss_fn
        self.hidden_dim = [layer_size, layer_size, layer_size]

        if isinstance(self.hidden_dim, int):
            self.hidden_dim = [self.hidden_dim]
        self.hidden_layers = nn.ModuleList(
            [
                nn.Linear(in_dim, out_dim)
                for in_dim, out_dim in zip(
                    [input_dim] + self.hidden_dim[:-1], self.hidden_dim
                )
            ]
        )
        self.output_layer = nn.Linear(self.hidden_dim[-1], output_dim)

    def forward(self, Te, T, Q_dot_in, T_target):
        x = th.cat([Te, T, Q_dot_in], dim=1)
        for layer in self.hidden_layers:
            x = layer(x)
            x = th.relu(x)
        x = self.output_layer(x)
        loss = self.loss_fn(x, T_target)
        return loss, x

    def convexify(self):
        pass

    def is_input_convex(self) -> bool:
        return False


class ResidualICNN(nn.Module):
    def __init__(self, layer_size: int):
        super(ResidualICNN, self).__init__()
        self.icnn = ICNN(3, 1, layer_size)
        self.loss_fn = nn.MSELoss()

    def forward(self, T_amb, T, Q_dot_in, T_target):
        dT_dt = self.icnn(th.cat([T_amb, T, Q_dot_in], dim=1))
        T_next = T + dT_dt
        loss = self.loss_fn(T_next, T_target)
        return loss, T_next

    def convexify(self):
        self.icnn.convexify()

    def is_input_convex(self) -> bool:
        return self.icnn.is_input_convex()


class BaselineModel(nn.Module):
    def __init__(
        self,
        loss_fn=nn.MSELoss(),
    ):
        super(BaselineModel, self).__init__()
        self.loss_fn = loss_fn
        self.dummy_param = nn.Parameter(th.tensor(0.1))

    def forward(self, Te, T, Q_dot_in, T_target):
        T_detached = T.detach()
        # Create a new tensor that requires gradients for internal computation
        T_comp = T_detached.clone().requires_grad_(True)
        loss = self.loss_fn(T_comp, T_target)
        return loss, T_comp

    def convexify(self):
        pass

    def is_input_convex(self) -> bool:
        return False


class RCModel(nn.Module):
    def __init__(
        self,
        loss_fn=nn.MSELoss(),
    ):
        super(RCModel, self).__init__()
        self.loss_fn = loss_fn
        self.R = nn.Parameter(th.tensor(50.0))
        self.C = nn.Parameter(th.tensor(1000.0))

    def forward(self, Te, T, Q_dot_in, T_target):
        Delta_T = (Te - T) / (self.R * self.C) + Q_dot_in / self.C
        T_next = T + Delta_T
        loss = self.loss_fn(T_next, T_target)
        return loss, T_next

    def convexify(self):
        pass

    def is_input_convex(self) -> bool:
        return False


class EnergyBasedICNN(nn.Module):
    def __init__(self, layer_size: int, loss_fn=nn.MSELoss()):
        super(EnergyBasedICNN, self).__init__()
        self.potential_func = ICNN(
            3,
            1,
            hidden_layer_sizes=layer_size,
        )
        self.loss_fn = loss_fn

    def forward(self, T_amb, T, Q_dot_in, T_target):
        # Detach T to prevent gradients from flowing back to input
        T_detached = T.detach()
        # Create a new tensor that requires gradients for internal computation
        T_comp = T_detached.clone().requires_grad_(True)

        Psi = self.potential_func(th.cat([T_amb, T_comp, Q_dot_in], dim=1))

        grad_outputs = th.ones_like(Psi)
        dPsi_dT = th.autograd.grad(
            Psi,
            T_comp,
            grad_outputs=grad_outputs,
            create_graph=True,
        )[0]

        # print(f"Nabla non-positive : {th.all(dPsi_dT <= 0)}")
        dT_dt = -dPsi_dT
        T_next = T_comp + dT_dt
        loss = self.loss_fn(T_next, T_target)
        return loss, T_next

    def convexify(self):
        self.potential_func.convexify()

    def is_input_convex(self) -> bool:
        return self.potential_func.is_input_convex()


if __name__ == "__main__":
    model = ICNN2(2, 1, hidden_dims=[8, 8, 8])
    print(model)
