from functools import cached_property

import pandas as pd
import pandera as pa
import plotly.express as px
import plotly.graph_objects as go

# import seaborn as sns
from alphabuilding.constants import Levels
from alphabuilding.control.performance_metrics import (
    hvac_control_performance_metrics,
)
from alphabuilding.control.types import SimulationPhase
from alphabuilding.domain.df_schemas import MpcSimulationResult, SimulationResult


class ControllerSimulationComparator:
    def __init__(
        self,
        *,
        mpc_results: pd.DataFrame | None = None,
        reference_results: pd.DataFrame | None = None,
        strict: bool = True,
        simulation_phase: SimulationPhase = SimulationPhase.EVALUATION,
    ):
        if strict:
            self._validate_inputs(mpc_results, reference_results)

        self.mpc_results = (
            mpc_results[mpc_results["simulation_phase"] == simulation_phase]
            if mpc_results is not None
            else None
        )
        self.reference_results = (
            reference_results[reference_results["simulation_phase"] == simulation_phase]
            if reference_results is not None
            else None
        )

    def _validate_inputs(
        self,
        mpc_results: pd.DataFrame | None,
        reference_results: pd.DataFrame | None,
    ) -> None:
        if mpc_results is not None:
            try:
                for _, df in mpc_results.groupby(level=Levels.experiment):
                    MpcSimulationResult.validate(df.droplevel(Levels.experiment))
            except pa.errors.SchemaError as e:
                raise ValueError(
                    "MPC results DataFrame does not conform to MpcSimulationResult schema."
                ) from e

        if reference_results is not None:
            SimulationResult.validate(reference_results)

        if mpc_results is not None and reference_results is not None:
            if (
                not mpc_results.index.droplevel(Levels.experiment)
                .isin(reference_results.index)
                .all()
            ):
                raise ValueError(
                    "MPC results contain timestamps not present in reference."
                )

            if not reference_results.index.isin(
                mpc_results.index.get_level_values(-1)
            ).all():
                raise ValueError(
                    "Reference result contains timestamps missing from MPC results."
                )

    @cached_property
    def pareto_data(self) -> pd.DataFrame:
        return self._compute_mpc_pareto_front()

    def _compute_mpc_pareto_front(self) -> pd.DataFrame:

        mpc_hvac_performance_metrics = []

        if self.mpc_results is not None:
            for experiment_id, df in self.mpc_results.groupby(level=Levels.experiment):
                single_controller_df = df.droplevel(Levels.experiment)

                metrics_df = hvac_control_performance_metrics(single_controller_df)

                metrics_df["experiment_id"] = experiment_id
                metrics_df["horizon"] = single_controller_df["horizon"].iloc[0]
                metrics_df["lambda_reg_eigvals"] = single_controller_df[
                    "lambda_reg_eigvals"
                ].iloc[0]
                metrics_df["T_margin"] = single_controller_df["Tmargin"].iloc[0]
                metrics_df["SolRad_std"] = single_controller_df["SolRad_std"].iloc[0]
                metrics_df["Tamb_std"] = single_controller_df["Tamb_std"].iloc[0]
                metrics_df["slack_weight"] = single_controller_df["slack_weight"].iloc[
                    0
                ]
                metrics_df["R_weight"] = single_controller_df["R_weight"].iloc[0]

                mpc_hvac_performance_metrics.append(metrics_df)

            return pd.concat(mpc_hvac_performance_metrics).set_index("experiment_id")
        else:
            raise ValueError("No MPC results available to compute Pareto front.")

    def sns_pareto(self) -> None:
        """generate pareto plot using seaborn. This is a static plot and not interactive like the plotly version."""
        pareto_data = self.pareto_data
        # Plot MPC Data
        fig = sns.scatterplot(
            data=pareto_data,
            x="total_energy_watt_hour",
            y="total_comfort_violation_kelvin_hours",
            hue=pareto_data["lambda_reg_eigvals"].astype(str),
            size="slack_weight",
            alpha=0.7,
        ).get_figure()

        # add reference controller if available
        if self.reference_results is not None:
            ref_metrics = hvac_control_performance_metrics(self.reference_results)
            fig_ax = fig.axes[0]
            fig_ax.scatter(
                ref_metrics["total_energy_watt_hour"],
                ref_metrics["total_comfort_violation_kelvin_hours"],
                color="red",
                marker="X",
                s=100,
                label="RBC Controller",
            )
            fig_ax.legend()

        fig.suptitle("MPC HVAC Control Pareto Front")
        fig.tight_layout()
        fig.show()

    def pareto_plot(self) -> None:
        """generate pareto plot using plotly express. This is an interactive plot that allows hovering to see experiment details."""
        pareto_data = self.pareto_data

        # Create interactive scatter plot with Plotly Express
        # hover_name displays the Index (experiment_id) at the top of the tooltip
        sorted_lambdas = sorted(pareto_data["lambda_reg_eigvals"].unique())
        pareto_data["lambda"] = pareto_data["lambda_reg_eigvals"].astype(str)

        fig = px.scatter(
            pareto_data.reset_index(),  # Reset index to make 'experiment_id' a column
            x="total_energy_watt_hour",
            y="total_comfort_violation_kelvin_hours",
            color="lambda",
            category_orders={"lambda": [str(x) for x in sorted_lambdas]},
            color_discrete_sequence=px.colors.qualitative.Safe,  # Good for distinct values    size="slack_weight",
            hover_name="experiment_id",  # This is the "name" of the model/experiment
            hover_data={
                "horizon": True,
                "T_margin": True,
                "SolRad_std": True,
                "Tamb_std": True,
                "slack_weight": True,
                "R_weight": True,
            },
            title="MPC HVAC Control Pareto Front",
            labels={
                "total_energy_watt_hour": "Total Energy [Wh]",
                "total_comfort_violation_kelvin_hours": "Comfort Violation [K·h]",
            },
            template="plotly_white",
            opacity=0.7,
        )

        # 3. Add reference controller if available using graph_objects
        if self.reference_results is not None:
            ref_metrics = hvac_control_performance_metrics(self.reference_results)
            fig.add_trace(
                go.Scatter(
                    x=ref_metrics["total_energy_watt_hour"],
                    y=ref_metrics["total_comfort_violation_kelvin_hours"],
                    mode="markers",
                    marker=dict(color="red", symbol="x", size=12),
                    name="Reference Controller",
                    hoverinfo="name+x+y",
                )
            )

        # 4. Show the interactive plot
        fig.show()

    def select_most_energy_efficient_mpc(self):
        experiment = self.pareto_data["total_energy_watt_hour"].idxmin()
        return experiment

    def select_least_energy_efficient_mpc(self):
        experiment = self.pareto_data["total_energy_watt_hour"].idxmax()
        return experiment

    def select_least_comfortable_mpc(self):
        experiment = self.pareto_data["total_comfort_violation_kelvin_hours"].idxmax()
        return experiment

    def select_most_comfortable_mpc(self):
        experiment = self.pareto_data["total_comfort_violation_kelvin_hours"].idxmin()
        return experiment
